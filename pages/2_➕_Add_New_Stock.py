import streamlit as st
import pandas as pd
import altair as alt
import yfinance as yf
from finta import TA
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Add New Stock", page_icon="➕")

f'''
# ➕Add New Stocks 
'''

def validate_stock():
    print(ticker, buy_date, shares, buy_price)

    if any([ticker is None, buy_date is None, shares is None, buy_price is None]):
        return st.error('Stock unsuccessfully added to portfolio!')
    else:
        return st.success('Stock successfully added to portfolio!')

with st.form("my_form", clear_on_submit=True):
    st.write("Please enter your position details...")

    ticker = buy_date = shares = buy_price = None

    ticker = st.text_input(label='Ticker', value=None)
    # if len(ticker.split(".")) == 0:
    #     ticker = ticker + ".SI"

    buy_date = st.date_input(label='Purchase Date', value=None)
    shares = st.number_input(label='Shares Purchased', value=None, step=1)
    buy_price = st.number_input(label='Purchase Price per Share', value=None)

    st.write("")
    st.form_submit_button('Submit stock')

st.write(ticker, buy_date, shares, buy_price)

if any([ticker is None, buy_date is None, shares is None, buy_price is None]):
    st.error('ERROR: One or more fields were left empty, or not in the correct format!')
else:
    ticker = str(ticker)
    if len(ticker.split(".")) == 1:
        ticker = ticker + ".SI"

    if buy_date > date.today():
        st.error(f'ERROR: Buy date must be today or before! You selected: {buy_date}')

    if (shares <= 0):
        st.error(f'ERROR: Shares Purchased must be greater than 0! You entered: {shares}')
    
    if (buy_price <= 0):
        st.error(f'ERROR: Price must be greater than 0! You entered: {buy_price}')

    ticker_df = yf.Ticker(ticker).history(start=buy_date, end=date.today())
    if ticker_df.empty:
        st.error(f'ERROR: Ticker can\'t be found! Ensure that you keyed in the correct symbol. You entered: {ticker.split(".")[0]}')
    
    prices = ticker_df.iloc[0][['High', 'Low']]
    if buy_price > prices.High:
        st.error(f'ERROR: Purchase price seems to be greater than the day\'s high price! You entered: {buy_price:.2f}, Day\'s High: {prices.High:.2f}')
    if buy_price < prices.Low:
        st.error(f'ERROR: Purchase price seems to be lower than the day\'s low price! You entered: {buy_price:.2f}, Day\'s Low: {prices.High:.2f}')
    
    st.success('Stock successfully added to portfolio!')