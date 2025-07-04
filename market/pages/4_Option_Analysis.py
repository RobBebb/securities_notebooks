from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    get_latest_ohlcv_using_ticker_id,
    retrieve_expiry_dates_using_ticker_id,
    retrieve_last_option_prices_using_stock_ticker_id_and_expiry_date_and_last_date,
    retrieve_options_using_ticker_id_and_expiry_date,
    retrieve_tickers_using_watchlist_code,
)

import streamlit as st

st.set_page_config(
    page_title="Options Analysis",
    layout="wide",
    # page_icon="👋",
)

st.title("Options Analysis")
st.subheader("Stock")

st.markdown("""Select a stock for analysing it's options.""")

WATCHLIST = "Options to Download"


# Get all tickers that have downloaded options
@st.cache_data
def cache_retrieve_tickers_using_watchlist_code(watchlist):
    return retrieve_tickers_using_watchlist_code(watchlist)


ticker_data = cache_retrieve_tickers_using_watchlist_code(WATCHLIST)
ticker_ids = [x[0] for x in ticker_data]
ticker_symbols = [x[1] for x in ticker_data]
ticker_names = [x[2] for x in ticker_data]
# Set defaults for ticker and date selection
default_selected_tickers = ticker_symbols[0]

today = datetime.now()
last_year = date(today.year - 1, 1, 1)
min_date = date(today.year - 5, 1, 1)
max_date = today

col1, col2, col3 = st.columns([0.33, 0.33, 0.34])

# Select a ticker
with col1:
    ticker = st.selectbox(
        "Select a symbol:",
        ticker_symbols,
    )
    if ticker:
        ticker_index = ticker_symbols.index(ticker)
        ticker_id = ticker_ids[ticker_index]
        ticker_name = ticker_names[ticker_index]

# Select dates
with col2:
    selected_dates = st.date_input(
        "Select dates for analysis:",
        (last_year, today),
        min_date,
        max_date,
        format="YYYY-MM-DD",
    )
    if selected_dates and len(selected_dates) == 1:
        start = selected_dates[0].strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

    elif selected_dates and len(selected_dates) == 2:
        start = selected_dates[0].strftime("%Y-%m-%d")
        end = selected_dates[1].strftime("%Y-%m-%d")
    else:
        st.write("No date selected.")


# Get ohlcv for the selected ticker
@st.cache_data
def cache_get_latest_ohlcv_using_ticker_id(ticker_id, name):
    ohlcv = get_latest_ohlcv_using_ticker_id(ticker_id)
    # Transform it a bit
    ohlcv = ohlcv.with_columns(pl.lit(name).alias("name"))
    # Reorder the columns
    ohlcv = ohlcv.select(["name", "date", "open", "high", "low", "close", "volume"])
    return ohlcv


ohlcv = cache_get_latest_ohlcv_using_ticker_id(ticker_id, ticker_name)

# Extract the last date a price is available for
last_date = ohlcv[0, 1]
last_close = ohlcv[0, 5]

# Configure the columns to display the ohlcv data
column_configuration = {
    "name": st.column_config.TextColumn("Name", help="Stock name", width=None),
    "date": st.column_config.DateColumn(
        "Date",
        help="Date the prices are for",
        format="iso8601",
        width="small",
    ),
    "open": st.column_config.NumberColumn(
        "Open",
        help="Opening price",
        format="$%.2f",
        width=None,
    ),
    "high": st.column_config.NumberColumn(
        "High",
        help="High price",
        format="$%.2f",
        width=None,
    ),
    "low": st.column_config.NumberColumn(
        "Low",
        help="Low price",
        format="$%.2f",
        width=None,
    ),
    "close": st.column_config.NumberColumn(
        "Close",
        help="Close price",
        format="$%.2f",
        width=None,
    ),
    "volume": st.column_config.NumberColumn(
        "Volume",
        help="Volume for the day",
        format="%d",
        width=None,
    ),
}

# Display the stock ohlcv data
st.dataframe(
    ohlcv,
    column_config=column_configuration,
)


# Get all option expiry dates for the selected ticker
@st.cache_data
def cache_retrieve_expiry_dates_using_ticker_id(ticker_id):
    return retrieve_expiry_dates_using_ticker_id(ticker_id)


expiry_dates = cache_retrieve_expiry_dates_using_ticker_id(ticker_id)

# Select the desired expiry_date
with col3:
    selected_expiry_date = st.selectbox(
        "Select an expiry_date:",
        expiry_dates,
        format_func=lambda x: x.strftime("%Y-%m-%d"),
    )


# Get all options and their prices for the selected ticker, expiry date and last date of prices
def cache_retrieve_last_option_prices_using_stock_ticker_id_and_expiry_date_and_last_date(
    ticker_id, expiry_date, last_date
):
    options = (
        retrieve_last_option_prices_using_stock_ticker_id_and_expiry_date_and_last_date(
            ticker_id, expiry_date, last_date
        )
    )
    options = options.with_columns(
        pl.when((pl.col("bid") == 0) | (pl.col("ask") == 0))
        .then(pl.col("last_price"))
        .otherwise((pl.col("bid") + pl.col("ask")) / 2.0)
        .alias("mid")
    )

    # Reorder the columns
    options = options.select(
        [
            "strike",
            "bid",
            "ask",
            "mid",
            "volume",
            "open_interest",
            "implied_volatility",
            "id",
            "call_put",
            "expiry_date",
            "date",
            "last_trade_date",
            "last_price",
            "change",
            "percent_change",
            "in_the_money",
        ]
    )

    return options


options = cache_retrieve_last_option_prices_using_stock_ticker_id_and_expiry_date_and_last_date(
    ticker_id, selected_expiry_date.strftime("%Y-%m-%d"), last_date
)

# Split the options up by calls and puts in a dictionary
partitions = options.partition_by("call_put", as_dict=True)

# Configure the options data display
column_configuration_options = {
    "strike": st.column_config.NumberColumn(
        "Strike Price",
        help="The exercise price of the option",
        format="$%.3f",
        width=None,
    ),
    "bid": st.column_config.NumberColumn(
        "Bid",
        help="The highest price a buyer is willing to pay",
        format="$%.3f",
        width=None,
    ),
    "ask": st.column_config.NumberColumn(
        "Ask",
        help="The lowest price a seller is willing to accept",
        format="$%.3f",
        width=None,
    ),
    "mid": st.column_config.NumberColumn(
        "Mid",
        help="The mid price between bid and ask",
        format="$%.3f",
        width=None,
    ),
    "volume": st.column_config.NumberColumn(
        "Volume",
        help="Volume for the day",
        format="%d",
        width=None,
    ),
    "open_interest": st.column_config.NumberColumn(
        "Open Interest",
        help="The number of option contracts that are currently held by traders in active positions.",
        format="%d",
        width=None,
    ),
    "implied_volatility": st.column_config.NumberColumn(
        "Implied Volatility",
        help="The expected price movement over a period of time. Ir is forward looking and represents future volatility expectations.",
        format="%.5f",
        width=None,
    ),
    "id": None,
    "call_put": None,
    "expiry_date": None,
    "date": None,
    "last_trade_date": None,
    "last_price": None,
    "change": None,
    "percent_change": None,
    "in_the_money": None,
}

# Extract the calls and puts from the dictionary
for key, value in partitions.items():
    # Display a dataframe of calls in the first column
    if key[0] == "C":
        calls = value
    if key[0] == "P":
        puts = value

st.subheader("Options")

# Columns for calls and puts
col1a, col2a = st.columns([0.5, 0.5])

with col1a:
    st.subheader("Calls")
    call_event = st.dataframe(
        calls,
        column_config=column_configuration_options,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )
# Display a dataframe of puts in the second column
with col2a:
    st.subheader("Puts")
    put_event = st.dataframe(
        puts,
        column_config=column_configuration_options,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )

st.subheader("Selected Options")

# selected_calls = call_event["selection"]["rows"]
selected_calls_indexes = call_event.selection.rows
selected_put_indexes = put_event.selection.rows

selected_calls = calls[selected_calls_indexes]
selected_puts = puts[selected_put_indexes]

col1b, col2b = st.columns([0.5, 0.5])

with col1b:
    st.subheader("Calls")
    st.dataframe(
        selected_calls,
        column_config=column_configuration_options,
        use_container_width=True,
        hide_index=True,
    )

with col2b:
    st.subheader("Puts")
    st.dataframe(
        selected_puts,
        column_config=column_configuration_options,
        use_container_width=True,
        hide_index=True,
    )
