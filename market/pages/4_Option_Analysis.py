from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    get_latest_ohlcv_using_ticker_id,
    retrieve_expiry_dates_using_ticker_id,
    retrieve_last_option_prices_using_stock_ticker_id_and_expiry_date_and_last_date,
    retrieve_tickers_using_watchlist_code,
)
from securities_notebooks.market.utils.option_strategy_calcs import (
    strategy_payoff_calcs,
    strategy_type_calcs,
)

import streamlit as st

risk_free_rate = 0.05
volatility = 0.2


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
expiry_dates = expiry_dates.with_columns(
    pl.col("expiry").dt.strftime("%Y-%m-%d").alias("expiry_date")
)

expiry_dates_list = expiry_dates.select("expiry_date").to_series().to_list()

st.subheader("Options")


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
        .alias("mid"),
        pl.lit(False).alias("buy"),
        pl.lit(False).alias("sell"),
    )

    # Reorder the columns
    options = options.select(
        [
            "expiry_date",
            "ticker",
            "strike",
            "bid",
            "ask",
            "mid",
            "volume",
            "open_interest",
            "implied_volatility",
            "id",
            "call_put",
            "date",
            "last_trade_date",
            "last_price",
            "change",
            "percent_change",
            "in_the_money",
            "buy",
            "sell",
        ]
    )

    return options


# Configure the options data display
buy_sell_column_configuration_options = {
    "ticker": None,
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
    "buy": st.column_config.CheckboxColumn(
        "Buy",
        help="Check if you wish to buy this option",
        default=False,
    ),
    "sell": st.column_config.CheckboxColumn(
        "Sell",
        help="Check if you wish to sell this option",
        default=False,
    ),
}


tabs = st.tabs(expiry_dates_list)
call_events = {}
put_events = {}
# Fill each tab with content
for i, tab in enumerate(tabs):
    with tab:
        selected_expiry_date = expiry_dates_list[i]
        options = cache_retrieve_last_option_prices_using_stock_ticker_id_and_expiry_date_and_last_date(
            ticker_id, selected_expiry_date, last_date
        )

        # Split the options up by calls and puts in a dictionary
        partitions = options.partition_by("call_put", as_dict=True)

        # Extract the calls and puts from the dictionary
        for key, value in partitions.items():
            # Display a dataframe of calls in the first column
            if key[0] == "C":
                calls = value
            if key[0] == "P":
                puts = value

        calls_tuple = calls.rows(named=True)
        puts_tuple = puts.rows(named=True)

        # Columns for calls and puts
        col1a, col2a = st.columns([0.5, 0.5])

        with col1a:
            st.subheader("Calls")
            call_events[i] = st.data_editor(
                calls_tuple,
                column_config=buy_sell_column_configuration_options,
                use_container_width=True,
                disabled=[
                    "ticker",
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
                ],
                hide_index=True,
                key=f"selected_calls_tuples{i}",
            )
        # Display a dataframe of puts in the second column
        with col2a:
            st.subheader("Puts")
            put_events[i] = st.data_editor(
                puts_tuple,
                column_config=buy_sell_column_configuration_options,
                use_container_width=True,
                disabled=[
                    "ticker",
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
                ],
                hide_index=True,
                key=f"selected_puts_tuples{i}",
            )

selected_options = []

for i in range(len(expiry_dates_list)):
    # get a list of options for each expiry_date
    call_event = call_events[i]
    put_event = put_events[i]

    for j in range(len(call_event)):
        # get one option
        event = call_event[j]
        # st.write(event)
        if event["buy"] or event["sell"]:
            selected_options.append(event)

    for k in range(len(put_event)):
        # get one option
        event = put_event[k]
        # st.write(event)
        if event["buy"] or event["sell"]:
            selected_options.append(event)

print(selected_options)

if not selected_options:
    st.warning("No options selected")
    st.stop()

selected_options = sorted(
    selected_options,
    # Sorting by sell means that options being bought are sorted first as false is sorted before true
    # and if sell is false then buy is true.
    key=lambda x: (x["expiry_date"], x["call_put"], x["sell"], x["strike"]),  # type: ignore
)

print(selected_options)

# Configure the options data display
selected_options_column_configuration_options = {
    "expiry_date": st.column_config.DateColumn(
        "Expiry Date",
        help="The date the option finishes.",
    ),
    "ticker": None,
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
    "date": None,
    "last_trade_date": None,
    "last_price": None,
    "change": None,
    "percent_change": None,
    "in_the_money": None,
    "buy": st.column_config.CheckboxColumn(
        "Buy",
        help="Check if you wish to buy this option",
        default=False,
    ),
    "sell": st.column_config.CheckboxColumn(
        "Sell",
        help="Check if you wish to sell this option",
        default=False,
    ),
}

st.subheader("Selected Options")

st.dataframe(
    selected_options,
    width=800,
    column_config=selected_options_column_configuration_options,
)

strategy_dict = strategy_type_calcs(selected_options)

strategy = strategy_dict["strategy"]
payment = strategy_dict["payment"]
maximum_risk = strategy_dict["maximum_risk"]
maximum_reward = strategy_dict["maximum_reward"]
breakeven = strategy_dict["breakeven"]
breakeven_down = strategy_dict["breakeven_down"]
breakeven_up = strategy_dict["breakeven_up"]
strategy_warning = strategy_dict["warning"]

if strategy_warning:
    st.warning(strategy_warning)
    st.stop()

total_payoff_df = strategy_payoff_calcs(
    selected_options=selected_options,
    last_close=last_close,
    risk_free_rate=risk_free_rate,
    volatility=volatility,
)

if total_payoff_df is not None:
    base = alt.Chart(total_payoff_df).properties(
        title={
            "text": strategy,
            "subtitle": [
                f"""Underlying: {ticker_name}, Current Stock Price: {last_close:.2f}""",
                f"""Payment: {payment}, Maximum Risk: {maximum_risk}, Maximum Reward: {maximum_reward}, Breakeven: {breakeven}""",
            ],
            "fontSize": 18,
            "subtitleFontSize": 14,
        },
        width=600,
        height=500,
    )
    line = base.mark_line(strokeWidth=1.5).encode(
        x=alt.X(
            "stock_price:Q",
            title="Stock Price",
        ),
        y=alt.Y(
            "profit:Q",
            title="Profit",
            scale=alt.Scale(zero=False),
        ),
        tooltip=["stock_price:Q", "Profit:Q"],
    )

    yrule = base.mark_rule(strokeDash=[2, 2], color="#B082D1").encode(y=alt.datum(0))
    xrule = base.mark_rule(strokeDash=[2, 2], color="#19C6E9").encode(
        x=alt.datum(last_close)
    )

    chart = (
        (line + yrule + xrule)
        .configure(background="#eaf3fb")
        .configure_axis(
            format=".2f",
            tickColor="#93CAFA",
            domainColor="#000000",
            gridColor="#93CAFA",
            labelColor="#000000",
            grid=True,
            labelFontSize=12.0,
            titleFontSize=20,
            ticks=True,
        )
    )

    st.altair_chart(chart)
