import streamlit as st
import pandas as pd
import altair as alt
import yfinance as yf
from finta import TA
from pathlib import Path
import datetime
from datetime import date
from streamlit_gsheets import GSheetsConnection
import numpy as np
import math

st.set_page_config(page_title="Edit Portfolio", page_icon="✒️")

f'''
# ✒️Edit Portfolio
* Only deleting of entries is supported for now
'''

if "save_portfolio" not in st.session_state:
    st.session_state.save_portfolio = False

st.cache_data.clear()

conn = st.connection("portfolio", type=GSheetsConnection)
P_meta = conn.read(dtype={'Close Date':'str'})
edited_df = st.data_editor(P_meta, 
                           num_rows="dynamic",
                           disabled=[col for col in P_meta.columns]
                        #    column_config = {
                        #        "Close Date": st.column_config.TextColumn(),
                        #        "Closed": st.column_config.SelectboxColumn(options=[False, True])}
                        )

if st.button("Save Portfolio", type="primary"):
    st.session_state.save_portfolio = True

    # # Checks
    # for i, row in edited_df.iterrows():
    #     if ((not row['Close Date'] == "") or (not math.isnan(row['Close Price']))):
    #         edited_df.loc[i, 'Closed'] = True

    #     if (row['Closed']) and ((row['Close Date'] == "") or (math.isnan(row['Close Price']))):
    #         st.error('ERROR: Closed position but no information of Close Date or Close Price!')
    #         st.session_state.save_portfolio = False
    #         break
    #     else:
    #         st.session_state.save_portfolio = True

if st.session_state.save_portfolio:
    conn.update(data=edited_df)
    st.success('Portfolio successfully updated!')
    st.cache_data.clear()
    st.session_state.save_portfolio = False