import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
import time

st.set_page_config(page_title="Mono - Transaction Classifier Testingr", page_icon="🤖")
st.title('TRANSACTION CLASSIFIER TESTING')

st.info('Hey There, please copy and paste less than 20 Transaction Data Obejects. See Example below 🥷', icon="ℹ️")
# Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False



def get_category(data):
    api_url = "http://txcc.withmono.com/transaction-classifier"
    output = requests.post(url=api_url, json=data)
    model_result = json.loads(output.text)
    return model_result

code = '''
{  "data": [
        {"_id": "62e90f5678d95406325411a7",
        "type": "debit",
        "amount": 10000,
        "narration": "00001322 VIA GTWORLD TO ABEGAPP CIROMA CHUKWUMA ADEKUNLE /10.75/REF:GW2148344014000000010022080212 F",
        "date": "2022-08-02T12:48:00.200Z",
        "balance": 0,
        "currency": "NGN"},
            ...
        ]
    }
'''
st.code(code, language='json')

with st.form("my_form", clear_on_submit=True):
   transaction_data = st.text_input(
    "Enter Transaction data object 👇",
    placeholder='''{ "data" : [ ... ] }
    ''',
    key="placeholder",
    label_visibility=st.session_state.visibility,
    disabled=st.session_state.disabled,
    )
   
   if transaction_data:
        st.write("Preview Input")
        st.json(transaction_data, expanded= False)
   submitted = st.form_submit_button("Categorize", disabled=st.session_state.disabled)
   if submitted:
        try:
            data = json.loads(transaction_data)
            len(data['data'])
            if len(data['data']) <= 20:
                    with st.spinner('Please Wait 🥱 ... '):
                        result = get_category(data)
                        st.markdown("[Analyze the Categories and Leave Your Feedback Here, Please ✌️](https://forms.gle/k1SbVFDXpPYJKpDY6)")
                        df = pd.json_normalize(result['data'])
                        st.dataframe(df)
                        st.balloons()
            else:
                st.error('🚨 You have inputed {} transaction which is more than 20, 🧐 Oya Please reduce it and try again so we can continue...'.format(len(data['data'])))
        except Exception as e:
             print(e)

cat_data = pd.read_csv('./category_data.csv')
st.write( "Category Definition")
st.dataframe(cat_data)

