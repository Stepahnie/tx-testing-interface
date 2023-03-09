import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridUpdateMode, GridUpdateMode, ColumnsAutoSizeMode, DataReturnMode, ColumnsAutoSizeMode, AgGridTheme
import numpy as np
import json
import requests

import s3fs
import os



st.set_page_config(page_title="Mono - Transaction Classifier Testingr", page_icon="🤖",   layout="wide",
   initial_sidebar_state="expanded")
st.title('TRANSACTION CLASSIFIER TESTING')

st.info('Hey there, kindly upload a JSON file containing Transaction Data Obejects (less than 20). See Example below  👇🏾')


fs = s3fs.S3FileSystem(anon=False)
bucket_name = 'mono-data-science/tx-classifier-testing-data'
data_file = 'tx-classifier-model-testing-data.csv'
bank_file = 'mono_banks.txt'
category_file ='categories.txt'



@st.cache_data (show_spinner=False)
def get_category(data):
    # with st.spinner('Please Hold on a little ... '):
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


with fs.open(f"{bucket_name}/{bank_file}", "r") as f:
    banks = [line.strip() for line in f.readlines()]

with fs.open(f"{bucket_name}/{category_file}", "r") as f:
    categories = [line.strip() for line in f.readlines()]

uploaded_file = st.file_uploader("Choose a JSON file", accept_multiple_files=False)
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()

    try:
        data = json.loads(bytes_data)
        st.write("pre-view file")
        st.json(data, expanded= False)
    except Exception as e:
        st.write(e)
        print(e)

    result = {}
    if  len(data['data'] )<= 20:
    # do API Call here
        with st.spinner(text="Fetching Categorisation"):
            try:
                cat_result = get_category(data)
            except Exception as e:
                st.write(e)

        result['data'] = cat_result['data']
    else:
        st.warning('🚨 You have inputed {} transaction which is more than 20, 🧐 Oya Please reduce it and try again so we can continue...'.format(len(data['data'])))
    
    option = st.selectbox(
    "What Bank's Data are you testing with?",
    (sorted(banks)))

    st.info('Review the Categories. Double-click the Category to select your prefered category', icon="ℹ️")
    df = pd.json_normalize(result['data'])
    data = df.loc[:, ['category', 'narration', 'amount', 'type']]
    # Define the column definitions for the Ag-Grid table

    column_defs = [
        {'field': 'category', 'editable': True,  'cellEditorPopupPosition': 'under',
        'cellEditor': 'agSelectCellEditor', 'cellEditorParams': {
            'values': sorted(categories)
        }},
        {'field': 'narration'},
        {'field': 'amount'},
        {'field': 'type'}
    ]

    # Define the Ag-Grid table configuration
    grid_options = {
        'columnDefs': column_defs,
        'rowData': data.to_dict('records'),
        'pagination': True,
        'paginationAutoPageSize': True,
        'domLayout': 'normal',
        'enableCellChangeFlash': True
    }
    
    custom_css = {
        ".ag-header-cell-text": {"font-size": "13px", 'text-overflow': 'revert;', 'font-weight': 700}, ".ag-theme-streamlit": {'transform': "scale(0.9)","transform-origin": '0 0'},
        ".ag-center-cols-container": {"font-size": "14px"},
    }
    # Render the Ag-Grid table
    grid_response = AgGrid(
        data, 
        grid_options,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        custom_css=custom_css,
        theme=AgGridTheme.ALPINE,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        header_checkbox_selection_filtered_only=True
    )

    grid_data = pd.DataFrame(grid_response["data"])
    grid_data['bank'] = option

    
    if option != '':
        submit = st.button('Submit Reviews...')
        if submit:
            # Load the existing CSV file from S3 into a Pandas DataFrame
            with st.spinner(text="..."):
                with fs.open(f"{bucket_name}/{data_file}", "rb") as f:
                    existing_data = pd.read_csv(f)
                appended_data = pd.concat([existing_data, grid_data], ignore_index=True)

                with fs.open(f"{bucket_name}/{data_file}", "w") as f:
                    appended_data.to_csv(f, index=False)
                
                    st.balloons()

                st.write('Feel free to upload and review another  set of Data')
                st.markdown("[Analyze the Categories and Leave Your Feedback Here, Pleas](https://forms.gle/k1SbVFDXpPYJKpDY6)")
    else:
        st.write('Please Select a Bank above to Proceed 👆🏾')



cat_data = pd.read_csv('./category_data.csv')
expander = st.expander("See Category Explanations")
expander.table( cat_data)






