import requests
import json
import pandas as pd
import streamlit as st

import numpy as np
import json
import requests

import s3fs
import os
import datetime



st.set_page_config(page_title="Mono - Transaction Classifier Testingr", page_icon="🤖",   layout="wide",
   initial_sidebar_state="expanded")
st.title('TRANSACTION CLASSIFIER TESTING')

st.info('Connect an account on Quickstart [See Here](https://quickstart.withmono.com/) ', icon="ℹ️")
fs = s3fs.S3FileSystem(anon=False)
bucket_name = 'mono-data-science/tx-classifier-testing-data'
data_file = 'tx-classifier-model-testing-data.csv'
bank_file = 'mono_banks.txt'
category_file ='categories.txt'
eval_data = 'model_scores.csv'



@st.cache_data (show_spinner=False)
def get_category(data):
    # with st.spinner('Please Hold on a little ... '):
    api_url = "http://txcc.withmono.com/transaction-classifier"
    try:
        output = requests.post(url=api_url, json=data)
        model_result = json.loads(output.text)
        return model_result
    except Exception as e:
        st.write(e)
        return e

@st.cache_data (show_spinner=False)


def get_transactions(account_id, mono_sec_key):
    url = f"https://api.withmono.com/accounts/{account_id}/transactions?limit=32"
    headers = {
        "Accept": "application/json",
        "mono-sec-key":  mono_sec_key
    }
    try:
        response = requests.get(url, headers=headers)
        meta_data = json.loads(response.text)
        return meta_data['data']
    except Exception as e:
        st.write(e)
        return e



with fs.open(f"{bucket_name}/{bank_file}", "r") as f:
    banks = [line.strip() for line in f.readlines()]

with fs.open(f"{bucket_name}/{category_file}", "r") as f:
    categories = [line.strip() for line in f.readlines()]
    categories.insert(0, '')

if 'stage' not in st.session_state:
    st.session_state.stage = 0

def set_stage(stage):
    st.session_state.stage = stage



if 'select_values' not in st.session_state:
    st.session_state.select_values = {}
res =[]
with st.form("my_form"):
    account_id = st.text_input('Enter Account ID', key='id')
    col1, col2 = st.columns([2, 2])

    with col2:
        bank = st.selectbox(
            "Select Bank", (sorted(banks)))

    with col1:
        country = st.selectbox(
            "Select Country", ('', 'Nigeria','Ghana','Kenya', 'South Africa'))


    get_trans = st.form_submit_button('Categorize', 
    on_click=set_stage, args=(1,))


    if st.session_state.stage > 0: 
        if country == 'Nigeria':
            mono_sec_key = 'live_sk_8tlpVYjA3ljKzb9pHVIA'
        elif country == 'Ghana':
            mono_sec_key = 'live_sk_YXBG37CET1gSQ9SHKKrp'
        elif country == 'Kenya':
            mono_sec_key = 'live_sk_ZGwN0IazPoNNyxdpxoqR'
        elif country == 'South Africa':
            mono_sec_key = 'live_sk_wQhAoRE7S6Er5EL80Ngc'
        
        with st.spinner(text="Processing ..."):
            res = get_transactions(account_id, mono_sec_key)
            _data = get_category({'data': res})
        final_data = _data['data']
        df = pd.DataFrame(final_data)

             
        for val in range(len(final_data)):
            col1, col2 = st.columns([1, 3])

            with col1:
                key = f'select_{val}'
                selected_val = st.selectbox(
                    'Select Prefered Category',
                    sorted(categories),
                    key=key
                )
                st.session_state.select_values[key] = selected_val
            
            with col2:
                hide_dataframe_row_index  = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
                st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

                st.dataframe(pd.DataFrame( 
                    {'Predicted Category': [final_data[val]['category']],
                        'Narration': [final_data[val]['narration']], 
                        'Type': [final_data[val]['type']], 
                        'Amount':[final_data[val]['amount']]
                    }), 
                    width=200,
                    use_container_width=True)
    
        submitted = st.form_submit_button("Submit Review",  args=(2,))

        if submitted and st.session_state.stage > 0:
            prefered_category = [val for val in st.session_state.select_values.values() ]
            collated_data = pd.DataFrame(df.loc[:, ['narration', 'amount', 'type','category']])
            collated_data['country'] = country
            collated_data['bank'] = bank
            collated_data['prefered category'] = prefered_category
            collated_data.rename(columns={'category':'predicted category'}, inplace=True)
            collated_data = collated_data.reindex(columns=['narration', 'amount', 'type', 'predicted category','prefered category'])
            
            evaluation_data = pd.DataFrame(columns=['session Id','correct predictions','incorrect predictions','score(over 100)'])

            test_id = 'test_Id_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')

            correct = [val for val in prefered_category if val == '' ]
            incorrect = [val for val in prefered_category if val != '' ]
            evaluation_data['session Id'] = [test_id]
            evaluation_data['correct predictions'] = [len(correct)]
            evaluation_data['incorrect predictions'] = [len(incorrect)]
            score = len(correct)/len(prefered_category) * 100
            evaluation_data['score(over 100)'] = [score]

            with st.spinner(text="..."):
                with fs.open(f"{bucket_name}/{data_file}", "rb") as f:
                    existing_data = pd.read_csv(f)
                appended_data = pd.concat([existing_data, collated_data], axis=0, join='inner')

                with fs.open(f"{bucket_name}/{data_file}", "w") as f:
                    appended_data.to_csv(f, index=False)

            with st.spinner(text="evaluating..."):
                with fs.open(f"{bucket_name}/{eval_data}", "rb") as f:
                    eval_existing_data = pd.read_csv(f)
                appended_data = pd.concat([eval_existing_data, evaluation_data], axis=0, join='inner')

                with fs.open(f"{bucket_name}/{eval_data}", "w") as f:
                    appended_data.to_csv(f, index=False)
                    st.balloons()

    
st.button('Reset Output', on_click=set_stage, args=(0,))
    
cat_data = pd.read_csv('./category_data.csv')
expander = st.expander("See Category Explanations")
expander.table( cat_data)
