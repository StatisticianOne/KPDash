import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from finta import TA
import math
from pathlib import Path
from datetime import date

pg = st.navigation([
    st.Page("streamlit_app.py", title="My Portfolio", icon="📈"),
    st.Page("pages/add_new_stock.py", title="Add New Stock", icon="➕"),
])

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='My Portfolio',
    page_icon=':chart_with_upwards_trend:', # This is an emoji shortcode. Could be a URL too.,
)

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
f'''
# 📈 Welcome! 

#### Here are your portfolio insights as of {pd.to_datetime(date.today()).strftime('%d %B %Y')}.
NOTE: Live market data might not be available during trading hours, expect (day-1) data instead.
'''

# Add some spacing
''
''
# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_portfolio():

    today = pd.to_datetime(date.today())
    DATA_FILENAME = Path(__file__).parent/'data/S&P 30-day Portfolio (NN v1.1).csv'
    P_meta = pd.read_csv(DATA_FILENAME)
    P_meta['Shares'] = 2

    all_stock_df = []
    for _, row in P_meta.iterrows():
        
        end_date = today if today <= pd.to_datetime(row['Expected Sell Date']) else pd.to_datetime(row['Expected Sell Date'])
        stock_df = yf.Ticker(row['Ticker']).history(start=pd.to_datetime(row['Buy Date']), end=end_date)
        stock_df['Ticker'] = '_'.join([row['Ticker'], row['Buy Date']])
        stock_df['Returns'] = ((stock_df['Close'].pct_change() + 1).cumprod() - 1)*100
        stock_df['Shares'] = 2
        stock_df['MV'] = stock_df['Shares'] * stock_df['Close']
        stock_df = stock_df.reset_index()
        stock_df['Date'] = stock_df['Date'].apply(lambda x: date(x.year, x.month, x.day))
        all_stock_df.append(stock_df)

    P = pd.concat(all_stock_df)

    return P, P_meta

P, P_meta = get_portfolio()

st.header('Overview', divider='gray')

cols = st.columns(2)

with cols[0]:
    total_in = (P_meta['Buy Price']*P_meta['Shares']).sum()
    latest_data = P.groupby('Ticker').last().sort_values('Ticker')
    current_value = (latest_data.Close * latest_data.Shares).sum()
    returns = (current_value / total_in - 1)*100

    st.metric(
            label='Current Portfolio Value',
            value=f'${current_value:.2f}',
            delta=f'{returns:.2f}%',
            delta_color='normal'
        )

with cols[1]:
    total_in = (P_meta['Buy Price']*P_meta['Shares']).sum()
    latest_data = P.groupby('Ticker').last()
    current_value = (latest_data.Close * latest_data.Shares).sum()
    returns = (current_value / total_in - 1)*100

    st.metric(
            label='Daily PnL',
            value=f'${current_value:.2f}',
            delta=f'{returns:.2f}%',
            delta_color='normal'
        )


''
''
''
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
        value=[min_value, max_value])
    filtered_date_P = filtered_stocks_P[(filtered_stocks_P.Date >= from_date) & (filtered_stocks_P.Date <= to_date)]

    # -------------- FORMATTING -------------- #
    plot_P = filtered_date_P.copy()
    plot_P.Date = plot_P.Date.apply(lambda x: str(x))

    # -------------- PRICE PLOT -------------- #
    st.line_chart(
        plot_P,
        x='Date',
        y='Close',
        color='Ticker',
    )

    # -------------- CUMU. RETURNS PLOT -------------- #
    st.line_chart(
        plot_P,
        x='Date',
        y='Returns',
        color='Ticker',
    )

    st.header('Current Market Value', divider='gray')

    cols = st.columns(5)

    for i, ticker in enumerate(selected_stocks):
        col = cols[i % len(cols)]

        with col:
            td_returns = round(filtered_stocks_P[filtered_stocks_P.Ticker == ticker].iloc[-1].Returns,2)
            current_value = filtered_stocks_P[filtered_stocks_P.Ticker == ticker].iloc[-1]['MV']

            st.metric(
                label=f'{ticker}',
                value=f'${current_value:.2f}',
                delta=f'{td_returns:.2f}%',
                delta_color='normal'
            )

    st.header('Daily PnL', divider='gray')

    cols = st.columns(5)

    for i, ticker in enumerate(selected_stocks):
        col = cols[i % len(cols)]

        with col:
            prev_value = filtered_stocks_P[filtered_stocks_P.Ticker == ticker].iloc[-2]['MV']
            current_value = filtered_stocks_P[filtered_stocks_P.Ticker == ticker].iloc[-1]['MV']
            daily_delta = current_value - prev_value
            daily_ret = (current_value/prev_value - 1)*100

            st.metric(
                label=f'{ticker}',
                value=f'${daily_delta:.2f}',
                delta=f'{daily_ret:.2f}%',
                delta_color='normal'
            )

    





















""
""
""
""




@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

gdp_df = get_gdp_data()



min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_df['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time', divider='gray')

''

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

''
''


first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

''

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )
