import select
from datetime import date, datetime
from operator import call

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    get_latest_ohlcv_using_ticker_id,
    retrieve_expiry_dates_using_ticker_id,
    retrieve_last_option_prices_using_stock_ticker_id_and_expiry_date_and_last_date,
    retrieve_options_using_ticker_id_and_expiry_date,
    retrieve_tickers_using_watchlist_code,
)
from trading_formations.option_utils.option import Option
from trading_formations.option_utils.option_calcs import option_calcs

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

st.write(f"Ticker: {ticker_name} ({ticker_id})")
# Extract the last date a price is available for
last_date = ohlcv[0, 1]
st.write(f"Last date for {ticker_name} ({ticker}): {last_date.strftime('%Y-%m-%d')}")
last_close = ohlcv[0, 5]
st.write(f"Last close price for {ticker_name} ({ticker}): ${last_close:.2f}")
st.write(f"Type: {type(last_close)}")


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

# st.dataframe(expiry_dates)

expiry_dates_list = expiry_dates.select("expiry_date").to_series().to_list()


# st.write(tabs)

# Select the desired expiry_date
# with col3:
#     selected_expiry_date = st.selectbox(
#         "Select an expiry_date:",
#         expiry_dates,
#         format_func=lambda x: x.strftime("%Y-%m-%d"),
#     )

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
# TODO: Use a dictionary to accumulate the selected options in the tabs
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

st.subheader("Selected Options")

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

if selected_options:
    selected_options = sorted(
        selected_options,
        # Sorting by sell means that options being bought are sorted first as false is sorted before true
        # and if sell is false then buy is true.
        key=lambda x: (x["expiry_date"], x["call_put"], x["sell"], x["strike"]),
    )
    st.dataframe(
        selected_options,
        column_config=buy_sell_column_configuration_options,
    )


if not selected_options:
    st.warning("No options selected to buy or sell.")
    st.stop()

strategy = ""

if len(selected_options) == 1:
    if selected_options[0]["call_put"] == "C":
        if selected_options[0]["buy"]:
            strategy = "Long Call"
        else:
            strategy = "Short (Naked) Call"
    else:
        if selected_options[0]["buy"]:
            strategy = "Long Put"
        else:
            strategy = "Short (Naked) Put"

if len(selected_options) == 2:
    if selected_options[0]["expiry_date"] == selected_options[1]["expiry_date"]:
        if (
            selected_options[0]["call_put"] == "C"
            and selected_options[1]["call_put"] == "C"
        ):
            if selected_options[0]["buy"] and selected_options[1]["buy"]:
                st.warning("Buying two calls is an unknown strategy.")
                st.stop()
            elif selected_options[0]["sell"] and selected_options[1]["sell"]:
                st.warning("Selling two calls is an unknown strategy.")
                st.stop()
            elif selected_options[0]["buy"]:
                if selected_options[0]["strike"] < selected_options[1]["strike"]:
                    strategy = "Bull Call Spread"
                elif (
                    selected_options[0]["buy"]
                    and selected_options[0]["strike"] > selected_options[1]["strike"]
                ):
                    strategy = "Bear Call Spread"
                else:
                    strategy = "Calendar Call"
                # TODO: Need to cater for diagonals
        elif (
            selected_options[0]["call_put"] == "P"
            and selected_options[1]["call_put"] == "P"
        ):
            if selected_options[0]["buy"] and selected_options[1]["buy"]:
                st.warning("Buying two puts is an unknown strategy.")
                st.stop()
            elif selected_options[0]["sell"] and selected_options[1]["sell"]:
                st.warning("Selling two puts is an unknown strategy.")
                st.stop()
            elif selected_options[0]["buy"]:
                if selected_options[0]["strike"] < selected_options[1]["strike"]:
                    strategy = "Bull Put Spread"
                elif (
                    selected_options[0]["buy"]
                    and selected_options[0]["strike"] > selected_options[1]["strike"]
                ):
                    strategy = "Bear Put Spread"
                else:
                    strategy = "Calendar Put"
                # TODO: Need to cater for diagonals
        else:
            if (
                selected_options[0]["call_put"] == "C"
                and selected_options[1]["call_put"] == "P"
            ):
                if selected_options[0]["buy"] and selected_options[1]["buy"]:
                    if selected_options[0]["strike"] == selected_options[1]["strike"]:
                        strategy = "Long Straddle"
                    elif selected_options[0]["strike"] != selected_options[1]["strike"]:
                        strategy = "Long Strangle"
                else:
                    st.warning("This is an unknown strategy. Do some more coding.")
                    st.stop()
                    # TODO: Need to cater for short straddles and strangles
    else:
        st.warning("Currently do not cater for calendar spreads. Do some more coding.")
        st.stop()

if len(selected_options) == 4:
    if (
        selected_options[0]["expiry_date"] == selected_options[1]["expiry_date"]
        and selected_options[2]["expiry_date"] == selected_options[3]["expiry_date"]
    ):
        if (
            selected_options[0]["call_put"] == "C"
            and selected_options[1]["call_put"] == "C"
            and selected_options[2]["call_put"] == "P"
            and selected_options[3]["call_put"] == "P"
        ):
            if (
                selected_options[0]["buy"]
                and selected_options[1]["sell"]
                and selected_options[3]["sell"]
                and selected_options[2]["buy"]
            ):
                if (
                    selected_options[0]["strike"]
                    > selected_options[1]["strike"]
                    > selected_options[3]["strike"]
                    > selected_options[2]["strike"]
                ):
                    strategy = "Long Iron Condor"
                elif (
                    selected_options[0]["strike"]
                    > selected_options[1]["strike"]
                    == selected_options[3]["strike"]
                    > selected_options[2]["strike"]
                ):
                    strategy = "Long Iron Butterfly"
                else:
                    st.warning("1.This is an unknown strategy. Do some more coding.")
                    st.stop()
            else:
                st.warning("2.This is an unknown strategy. Do some more coding.")
                st.stop()
        else:
            st.warning("3.This is an unknown strategy. Do some more coding.")
            st.stop()
    else:
        st.warning("4.This is an unknown strategy. Do some more coding.")
        st.stop()

st.subheader(f"Stratgey is: {strategy}")

# TODO: Need to loop through the selected options and work out the range of strikes
# TODO: and then use the range to work out the step size

min_strike = selected_options[0]["strike"]
max_strike = selected_options[0]["strike"]
for i in range(len(selected_options)):
    if selected_options[i]["strike"] < min_strike:
        min_strike = selected_options[i]["strike"]
    if selected_options[i]["strike"] > max_strike:
        max_strike = selected_options[i]["strike"]

start_price = min_strike - (min_strike * 0.05)
end_price = max_strike + (max_strike * 0.05)

# start_price = self.stock_price - (self.stock_price * 0.10)
# end_price = self.stock_price + (self.stock_price * 0.10)
steps = 100
step_size = (end_price - start_price) / steps
stock_prices = [start_price + i * step_size for i in range(steps)]

total_payoff = [0 for i in range(len(stock_prices))]

for i in range(len(selected_options)):
    option_id = selected_options[i]["id"]
    option_ticker = selected_options[i]["ticker"]
    option_strike = selected_options[i]["strike"]
    option_call_put = selected_options[i]["call_put"]
    option_expiry_date = selected_options[i]["expiry_date"]
    option_mid = selected_options[i]["mid"]

    option = Option(
        option_id, option_ticker, option_strike, option_expiry_date, option_call_put
    )
    option_calc = option_calcs(
        option, last_close, risk_free_rate=risk_free_rate, volatility=volatility
    )
    payoff = option_calc.payoff(stock_prices)
    if selected_options[i]["buy"]:
        # total_premium = total_premium - option_mid
        for j in range(len(stock_prices)):
            total_payoff[j] = total_payoff[j] + payoff[j] - option_mid
    else:
        # total_premium = total_premium + option_mid
        for j in range(len(stock_prices)):
            total_payoff[j] = total_payoff[j] - payoff[j] + option_mid

total_payoff_df = pl.DataFrame({"stock_price": stock_prices, "profit": total_payoff})


if total_payoff_df is not None:
    # line_chart = (
    #     alt.Chart(total_payoff_df)
    #     .mark_line(strokeWidth=1.5)
    #     .encode(
    #         x=alt.X(
    #             "stock_price:Q",
    #             title="Stock Price",
    #             axis=alt.Axis(
    #                 labelAngle=-45,
    #                 tickColor="#09080B",
    #                 domainColor="#09080B",
    #                 grid=True,
    #                 labelFontSize=10,
    #                 titleFontSize=12,
    #             ),
    #         ),
    #         y=alt.Y(
    #             "profit:Q",
    #             title="Profit",
    #             scale=alt.Scale(zero=False),
    #             axis=alt.Axis(
    #                 format=".2f",
    #                 tickColor="#09080B",
    #                 domainColor="#09080B",
    #                 gridColor="#9DCDF8",
    #                 grid=True,
    #                 labelFontSize=10,
    #                 titleFontSize=12,
    #             ),
    #         ),
    #         tooltip=["stock_price:Q", "Profit:Q"],
    #     )
    # ).properties(
    #     title={
    #         "text": strategy,
    #         "subtitle": [
    #             f"Option Ticker: {option_ticker}, Strike: {option_strike}, Expiry: {option_expiry_date}, Underlying: {ticker_name}, Current Stock Price: {last_close:.2f}"
    #         ],
    #         "fontSize": 16,
    #     },
    #     width=600,
    #     height=500,
    # )
    # yrule = (
    #     alt.Chart().mark_rule(strokeDash=[2, 2], color="#9219E9").encode(y=alt.datum(0))
    # )

    base = alt.Chart(total_payoff_df).properties(
        title={
            "text": strategy,
            "subtitle": [
                f"Option Ticker: {option_ticker}, Strike: {option_strike}, Expiry: {option_expiry_date}, Underlying: {ticker_name}, Current Stock Price: {last_close:.2f}"
            ],
            "fontSize": 16,
        },
        width=600,
        height=500,
    )
    line = base.mark_line(strokeWidth=1.5).encode(
        x=alt.X(
            "stock_price:Q",
            title="Stock Price",
            axis=alt.Axis(
                labelAngle=-45,
                tickColor="#09080B",
                domainColor="#09080B",
                grid=True,
                labelFontSize=10,
                titleFontSize=12,
            ),
        ),
        y=alt.Y(
            "profit:Q",
            title="Profit",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                format=".2f",
                tickColor="#09080B",
                domainColor="#09080B",
                gridColor="#9DCDF8",
                grid=True,
                labelFontSize=10,
                titleFontSize=12,
            ),
        ),
        tooltip=["stock_price:Q", "Profit:Q"],
    )
    yrule = base.mark_rule(strokeDash=[2, 2], color="#B082D1").encode(y=alt.datum(0))
    xrule = base.mark_rule(strokeDash=[2, 2], color="#19C6E9").encode(
        x=alt.datum(last_close)
    )

    chart = line + yrule + xrule
    st.altair_chart(chart)
