import streamlit as st
import pandas as pd
import altair as alt
import yfinance as yf
from finta import TA
from pathlib import Path
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Add New Stock", page_icon="➕")

f'''
# ➕Add New Stocks 
* Only supports SG stocks for now
'''

st.cache_data.clear()

conn = st.connection("portfolio", type=GSheetsConnection)
success = False

with st.form("my_form", clear_on_submit=True):
    st.write("Please enter your position details...")

    ticker = st.text_input(label='Ticker', value=None)

    buy_date = st.date_input(label='Purchase Date', value=None)
    shares = st.number_input(label='Number of Shares Purchased', step=1, value=None)
    buy_price = st.number_input(label='Purchase Price per Share', value=None)

    fields = {
        "ticker":ticker,
        "buy_date":buy_date,
        "shares":shares,
        "buy_price":buy_price
    }

    st.write("")
    submitted = st.form_submit_button('Submit stock')

if submitted:
    if any([ticker is None, shares is None, buy_price is None]):
        st.error('ERROR: One or more fields were left empty, or not in the correct format!')
    else:
        ticker = str(ticker)
        if len(ticker.split(".")) == 1:
            ticker = ticker.upper() + ".SI"

        if buy_date is None:
            buy_date = date.today() - pd.Timedelta(days=1)
            no_buy_date_flag = True

        if buy_date >= date.today():
            st.error(f'ERROR: Buy date must be before today (due to having no access to live data)! You selected: {buy_date}')

        elif date.weekday(buy_date) >= 5:
            st.error(f'ERROR: Buy date must be a trading day (i.e. weekday)!')

        elif (shares <= 0):
            st.error(f'ERROR: Shares Purchased must be greater than 0! You entered: {shares}')

        elif (buy_price <= 0):
            st.error(f'ERROR: Price must be greater than 0! You entered: {buy_price}')

        else:
            ticker_df = yf.Ticker(ticker).history(start=buy_date, end=date.today())
            if ticker_df.empty:
                st.error(f'ERROR: Ticker can\'t be found! Ensure that you keyed in the correct symbol, or that the date is not a non-trading day (e.g. public holidays). You entered: {ticker.split(".")[0]}')
            else:

                prices = ticker_df.iloc[0][['High', 'Low']]
                if (buy_price > prices.High) and (not no_buy_date_flag):
                    st.error(f'ERROR: Purchase price seems to be greater than the day\'s high price! You entered: {buy_price:.3f}, Day\'s High: {prices.High:.3f}')
                elif (buy_price < prices.Low) and (not no_buy_date_flag):
                    st.error(f'ERROR: Purchase price seems to be lower than the day\'s low price! You entered: {buy_price:.3f}, Day\'s Low: {prices.High:.3f}')
                else:           
                    success = True
                    P_meta = conn.read()

                    if no_buy_date_flag:
                        dual_key = '_'.join([ticker, f'{shares}@${buy_price:.3f}'])
                    else:
                        dual_key = '_'.join([ticker, str(buy_date)])

                    if dual_key in P_meta.dual_key.unique():

                        index = P_meta[P_meta['dual_key'] == dual_key].index
                        old_price = P_meta[P_meta['dual_key'] == dual_key]['Buy Price'].iloc[0]
                        old_shares = P_meta[P_meta['dual_key'] == dual_key]['Shares'].iloc[0]

                        P_meta.loc[index, 'Buy Price'] = buy_price
                        P_meta.loc[index, 'Shares'] = shares
                        
                        conn.update(data=P_meta)

                        st.cache_data.clear()
                        st.warning(f'WARNING: Stock and Purchase Date exists in portfolio: {old_shares} shares @ \${old_price}/share; Replaced with {shares} shares @ \${buy_price}/share.')
                    else:
                        new_data = pd.DataFrame([[ticker, buy_date, buy_price, shares, False, dual_key]], columns=['Ticker', 'Buy Date', 'Buy Price', 'Shares', 'Closed', 'dual_key'])

                        new_P = pd.concat([P_meta, new_data])
                        conn.update(data=new_P)

                        st.cache_data.clear()
                        st.success('Stock successfully added to portfolio!')
                
                no_buy_date_flag = False