import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
import time
from io import StringIO
from st_aggrid import AgGrid, GridUpdateMode, GridUpdateMode, ColumnsAutoSizeMode, DataReturnMode, ColumnsAutoSizeMode, AgGridTheme
from st_aggrid.grid_options_builder import GridOptionsBuilder



st.set_page_config(page_title="Mono - Transaction Classifier Testingr", page_icon="🤖",   layout="wide",
   initial_sidebar_state="expanded")
st.title('TRANSACTION CLASSIFIER TESTING')

st.info('Hey there, kindly upload a JSON file containing Transaction Data Obejects. See Example below 🥷', icon="ℹ️")



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




uploaded_file = st.file_uploader("Choose a JSON file", accept_multiple_files=False)
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
   
    try:
        data = json.loads(bytes_data)
        st.write("view uploaded file")
        st.json(data, expanded= False)
    except Exception as e:
        st.write(e)
        print(e)

    result = {}
    if  len(data['data'] )<= 20:
        # do API Call here
        with st.spinner(text="Fetching measures"):
            cat_result = get_category(data)
        
        result['data'] = cat_result['data']
    else:
        st.warning('🚨 You have inputed {} transaction which is more than 20, 🧐 Oya Please reduce it and try again so we can continue...'.format(len(data['data'])))
    st.markdown("[Analyze the Categories and Leave Your Feedback Here, Please ✌️](https://forms.gle/k1SbVFDXpPYJKpDY6)")
    df = pd.json_normalize(result['data'])

    gb = GridOptionsBuilder.from_dataframe(df.loc[:, ['category','narration','amount']])
    gb.configure_default_column(cellStyle={'color': 'black', 'font-size': '11px'}, suppressMenu=True, wrapHeaderText=True, autoHeaderHeight=True)
    custom_css = {".ag-header-cell-text": {"font-size": "11px", 'text-overflow': 'revert;', 'font-weight': 500},
      ".ag-theme-streamlit": {'transform': "scale(0.7)", "transform-origin": '0 0'}}
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar()
    gridoptions = gb.build()

    grid_table = AgGrid(
        df,
        custom_css=custom_css,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme=AgGridTheme.BALHAM,
        gridOptions=gridoptions,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,

        header_checkbox_selection_filtered_only=True,
    )
    sel_row = grid_table["selected_rows"]
    st.write(sel_row)
    v = grid_table['selected_rows']


cat_data = pd.read_csv('./category_data.csv')
expander = st.expander("See Category Explanations")
expander.table( cat_data)

# progress_text = "Operation in progress. Please wait."
# my_bar = st.progress(0, text=progress_text)

# for percent_complete in range(100):
#     time.sleep(0.1)
#     my_bar.progress(percent_complete + 1, text=progress_text)