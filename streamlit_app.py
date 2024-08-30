import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from finta import TA
import math
from pathlib import Path
from datetime import date
import altair as alt

pg = st.navigation([
    st.Page("streamlit_app.py", title="My Portfolio", icon="📈"),
    st.Page("pages/add_new_stock.py", title="Add New Stock", icon="➕")
])

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='My Portfolio',
    page_icon=':chart_with_upwards_trend:', # This is an emoji shortcode. Could be a URL too.,
    # layout='wide'
)
# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
f'''
# 📈 Welcome! 

#### Here are your portfolio insights as of {pd.to_datetime(date.today()).strftime('%d %B %Y')}.
* Live market data might not be available during trading hours, expect (day-1) data instead.
* Tickers with * denotes positions that have been closed.
'''

# Add some spacing
''
''
# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data(ttl=3600)
def get_portfolio():

    today = pd.to_datetime(date.today())
    DATA_FILENAME = Path(__file__).parent/'data/S&P 30-day Portfolio (NN v1.1).csv'
    P_meta = pd.read_csv(DATA_FILENAME)

    all_stock_df = []
    for _, row in P_meta.iterrows():
        
        end_date = today if not row['Closed'] else pd.to_datetime(row['Close Date'])
        stock_df = yf.Ticker(row['Ticker']).history(start=pd.to_datetime(row['Buy Date']), end=end_date)
        stock_df['Ticker'] = '_'.join([row['Ticker'], row['Buy Date']])
        stock_df['Returns'] = (stock_df['Close'] / row['Buy Price'] - 1)*100
        stock_df['MV'] = row['Shares'] * stock_df['Close']
        stock_df = stock_df.reset_index()
        stock_df['Date'] = stock_df['Date'].apply(lambda x: date(x.year, x.month, x.day))
        all_stock_df.append(stock_df)

    P = pd.concat(all_stock_df)
    
    realized_keys = P_meta[P_meta.Closed == True]['dual_key'].to_list()
    P_realized = P[P.Ticker.isin(realized_keys)].sort_values(['Ticker', 'Date'])
    P_unrealized = P[~P.Ticker.isin(realized_keys)].sort_values(['Ticker', 'Date'])

    P = pd.concat([P_realized, P_unrealized])

    return P_meta, P_realized, P_unrealized, P

P_meta, P_realized, P_unrealized, P = get_portfolio()

#################################################################################################################
st.header('Daily PnL', divider='gray')

pnl = P_unrealized.groupby('Ticker').agg({
    'Returns': lambda x: ((x.iloc[-1]/100+1) / (x.iloc[-2]/100+1) - 1)*100,
    'MV': lambda x: (x.iloc[-1] - x.iloc[-2])/1000
}).rename(columns={'Returns':'Daily Return [%]', 'MV':'Daily PnL [K]'})

cols = st.columns(1)
with cols[0]:
    value = pnl['Daily PnL [K]'].sum()
    prev_mv = P_unrealized.groupby('Ticker').apply(lambda x: x.iloc[-2])['MV'].sum()
    current_mv = P_unrealized.groupby('Ticker').last()['MV'].sum()
    delta = (current_mv / prev_mv - 1)*100

    st.metric(
                label=f'Portfolio\'s 1-day Change',
                value=f'${value:.3f}K',
                delta=f'{delta:.2f}%',
                delta_color='normal'
            )
''
pnl = pnl.style.map(lambda x: f"color: {'green' if x>=0 else 'red'}", subset=['Daily Return [%]', 'Daily PnL [K]'])\
    .format(precision=3)
st.dataframe(pnl, width=500)

''
''
''
#################################################################################################################

#################################################################################################################
st.header('Overview', divider='gray')

cols = st.columns(3)

# Realized + Unrealized Portfolio
with cols[0]:
    total_in = (P_meta['Buy Price']*P_meta['Shares']).sum()
    latest_data = P.groupby('Ticker').last().sort_values('Ticker')
    value = latest_data.MV.sum()
    mv_delta = (value - total_in)
    returns = (value / total_in - 1)*100
    delta_color = 'normal'

    st.metric(
            label='Combined Portfolio',
            value=f'${value/1000:.2f}K',
            delta=f'{mv_delta/1000:.2f}K | {returns:.2f}%',
            delta_color=delta_color
        )

# Unrealized Portfolio
with cols[1]:
    keys = P_unrealized.Ticker.unique()
    P_unrealized_meta = P_meta[P_meta.dual_key.isin(keys)]

    total_in = (P_unrealized_meta['Buy Price']*P_unrealized_meta['Shares']).sum()
    latest_data = P_unrealized.groupby('Ticker').last().sort_values('Ticker')
    value = latest_data.MV.sum()
    mv_delta = (value - total_in)
    returns = (value / total_in - 1)*100
    delta_color = 'normal'

    st.metric(
            label='Unrealized Portfolio',
            value=f'${value/1000:.2f}K',
            delta=f'{mv_delta/1000:.2f}K | {returns:.2f}%',
            delta_color=delta_color
        )

# Realized Portfolio
with cols[2]:
    if P_realized.empty:
        value = 0
        mv_delta = 0
        returns = 0
        delta_color = 'off'
    else:
        keys = P_realized.Ticker.unique()
        P_realized_meta = P_meta[P_meta.dual_key.isin(keys)]

        total_in = (P_realized_meta['Buy Price']*P_realized_meta['Shares']).sum()
        latest_data = P_realized.groupby('Ticker').last().sort_values('Ticker')
        value = latest_data.MV.sum()
        mv_delta = (value - total_in)
        returns = (value / total_in - 1)*100
        delta_color = 'normal'

    st.metric(
            label='Realized Portfolio',
            value=f'${value/1000:.2f}K',
            delta=f'{mv_delta/1000:.2f}K | {returns:.2f}%',
            delta_color=delta_color
        )

returns_df = P.groupby('Ticker').last()[['Returns', 'MV']]
# st.table(returns_df)
gainers_df = returns_df[returns_df.Returns > 0].sort_values('Returns', ascending=False).head().reset_index()
losers_df = returns_df[returns_df.Returns < 0].sort_values('Returns').head().reset_index()
''
''

'### Biggest Gainers (by %)'
cols = st.columns(5)
for i, row in gainers_df.iterrows():
    with cols[i]:
        key = row.Ticker
        total_in = (P_meta[P_meta.dual_key == key]['Buy Price'] * P_meta[P_meta.dual_key == key]['Shares']).iloc[0]
        value = row['MV']
        mv_delta = (value - total_in)
        returns = row['Returns']
        delta_color = 'normal'

        st.metric(
                label=f'{key}',
                value=f'${mv_delta/1000:.2f}K',
                delta=f'{returns:.2f}%',
                delta_color=delta_color
            )

''
''

'### Biggest Losers (by %)'
cols = st.columns(5)
for i, row in losers_df.iterrows():
    with cols[i]:
        key = row.Ticker
        total_in = (P_meta[P_meta.dual_key == key]['Buy Price'] * P_meta[P_meta.dual_key == key]['Shares']).iloc[0]
        value = row['MV']
        mv_delta = (value - total_in)
        returns = row['Returns']
        delta_color = 'normal'

        st.metric(
                label=f'{key}',
                value=f'${mv_delta/1000:.2f}K',
                delta=f'{returns:.2f}%',
                delta_color=delta_color
            )

''
''
'### Portfolio Value Growth'
min_value = P['Date'].min()
max_value = P['Date'].max()
from_date, to_date = st.slider(
    'Which date range are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

P_growth = P.groupby('Date').agg({'MV':'sum'}).apply(lambda x: x/1000).loc[from_date:to_date].reset_index()
P_growth.Date = P_growth.Date.apply(lambda x: str(x))

c = (
   alt.Chart(P_growth)
   .mark_line()
   .encode(x="Date", y=alt.Y("MV:Q", scale=alt.Scale(zero=False), title='Portfolio Market Value [K]'))
)

st.altair_chart(c, use_container_width=True)
''
''
''
#################################################################################################################

#################################################################################################################
st.header('Drill Down', divider='gray')

# -------------- STOCK FILTER -------------- #

container = st.container()
all = st.checkbox("Select all")
 
if all:
    selected_stocks = container.multiselect(
        'Which stocks would you like to view?',
        sorted(P.Ticker.unique()),
        sorted(P.Ticker.unique())
    )
else:
    selected_stocks = container.multiselect(
        'Which stocks would you like to view?',
        sorted(P.Ticker.unique()),
        sorted(P.Ticker.unique())[0]
    )

if len(selected_stocks) != 0:

    filtered_stocks_P = P[P.Ticker.isin(selected_stocks)]

    # -------------- DATE FILTER -------------- #
    min_value = filtered_stocks_P['Date'].min()
    max_value = filtered_stocks_P['Date'].max()
    from_date, to_date = st.slider(
        'Which date range are you interested in?',
        min_value=min_value,
        max_value=max_value,
        value=[min_value, max_value],
        key='drill_down')
    filtered_date_P = filtered_stocks_P[(filtered_stocks_P.Date >= from_date) & (filtered_stocks_P.Date <= to_date)]

    # -------------- FORMATTING -------------- #
    plot_P = filtered_date_P.copy()
    plot_P.Date = plot_P.Date.apply(lambda x: str(x))

    # -------------- PRICE PLOT -------------- #
    # st.line_chart(
    #     plot_P,
    #     x='Date',
    #     y='Close',
    #     color='Ticker',
    # )

    c = (
        alt.Chart(plot_P)
        .mark_line()
        .encode(x="Date", y=alt.Y("Close:Q", scale=alt.Scale(zero=False)), color="Ticker")
    )
    st.altair_chart(c, use_container_width=True)

    # -------------- CUMU. RETURNS PLOT -------------- #
    # st.line_chart(
    #     plot_P,
    #     x='Date',
    #     y='Returns',
    #     color='Ticker',
    # )
    c = (
        alt.Chart(plot_P)
        .mark_line()
        .encode(x="Date", y=alt.Y("Returns:Q", scale=alt.Scale(zero=False)), color="Ticker")
    )
    st.altair_chart(c, use_container_width=True)

    '### Stock Market Value and % Growth'
    ''
    cols = st.columns(5)

    for i, ticker in enumerate(selected_stocks):
        col = cols[i % len(cols)]

        with col:
            td_returns = round(filtered_stocks_P[filtered_stocks_P.Ticker == ticker].iloc[-1].Returns,2)
            current_value = filtered_stocks_P[filtered_stocks_P.Ticker == ticker].iloc[-1]['MV']

            st.metric(
                label=f'{ticker}',
                value=f'${current_value/1000:.2f}K',
                delta=f'{td_returns:.2f}%',
                delta_color='normal'
            )