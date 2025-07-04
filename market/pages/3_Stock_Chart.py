from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    retrieve_exchange_ids_using_country_alpha_3,
    retrieve_ohlcv_using_ticker_id_and_dates,
    retrieve_ticker_types,
    retrieve_tickers_using_exchanges_and_ticker_types,
    retrieve_unique_country_alpha_3_from_exchanges,
)

import streamlit as st

st.set_page_config(
    page_title="Stock Chart",
    layout="wide",
)

st.title("Stock Chart")

countries = retrieve_unique_country_alpha_3_from_exchanges()
country_codes = countries["country_alpha_3"].to_list()
ticker_types = retrieve_ticker_types()
ticker_type_ids = ticker_types["id"].to_list()
ticker_type_codes = ticker_types["code"].to_list()

col1, col2, col3, col4 = st.columns([0.25, 0.3, 0.2, 0.25])

with col1:
    country = st.pills(
        "Select a country to get symbols:",
        country_codes,
        selection_mode="single",
        default=country_codes[5],
    )

with col2:
    ticker_type = st.pills(
        "Select a ticker type to get symbols:",
        ticker_type_codes,
        selection_mode="single",
        default=ticker_type_codes[6],
    )

    if ticker_type:
        ticker_type_index = ticker_type_codes.index(ticker_type)
        ticker_type_id = ticker_type_ids[ticker_type_index]

if country:
    exchanges = retrieve_exchange_ids_using_country_alpha_3(country)
    exchange_ids = exchanges["id"].to_list()

tickers = retrieve_tickers_using_exchanges_and_ticker_types(
    exchange_ids, ticker_type_id
)
ticker_ids = tickers["id"].to_list()
ticker_symbols = tickers["ticker"].to_list()
ticker_names = tickers["name"].to_list()

with col3:
    ticker = st.selectbox(
        "Select a symbol:",
        ticker_symbols,
    )
    if ticker:
        ticker_index = ticker_symbols.index(ticker)
        ticker_id = ticker_ids[ticker_index]
        ticker_name = ticker_names[ticker_index]

today = datetime.now()
last_year = date(today.year - 1, 1, 1)
min_date = date(today.year - 5, 1, 1)
max_date = today

with col4:
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

moving_averages = []

col1a, col2a = st.columns([0.5, 0.5])


with col1a:
    st.write("Specify periods for simple moving averages. Set to zero if not required.")
    col1b, col2b, col3b, col4b = st.columns([0.25, 0.25, 0.25, 0.25])
    with col1b:
        ma1 = st.number_input(
            ":blue[SMA 1]",
            value=None,
            step=1,
            key="sma1",
        )
        if ma1:
            moving_averages.append(ma1)
    with col2b:
        ma2 = st.number_input(":orange[SMA 2]", value=None, step=1, key="sma2")
        if ma2:
            moving_averages.append(ma2)
    with col3b:
        ma3 = st.number_input(":red[SMA 3]", value=None, step=1, key="sma3")
        if ma3:
            moving_averages.append(ma3)
    with col4b:
        ma4 = st.number_input(":violet[SMA 4]", value=None, step=1, key="sma4")
        if ma4:
            moving_averages.append(ma4)

emas = []

with col2a:
    st.write(
        "Specify periods for exponential moving averages. Set to zero if not required."
    )
    col1c, col2c, col3c, col4c = st.columns([0.25, 0.25, 0.25, 0.25])
    with col1c:
        ema1 = st.number_input(
            ":blue[EMA 1]",
            value=None,
            step=1,
            key="ema1",
        )
        if ema1:
            emas.append(ema1)
    with col2c:
        ema2 = st.number_input(":orange[EMA 2]", value=None, step=1, key="ema2")
        if ema2:
            emas.append(ema2)
    with col3c:
        ema3 = st.number_input(":red[EMA 3]", value=None, step=1, key="ema3")
        if ema3:
            emas.append(ema3)
    with col4c:
        ema4 = st.number_input(":violet[EMA 4]", value=None, step=1, key="ema4")
        if ema4:
            emas.append(ema4)


@st.cache_data
def load_data(ticker_id, start, end):
    data = retrieve_ohlcv_using_ticker_id_and_dates(ticker_id, start, end)

    return data


data = load_data(ticker_id, start, end)
data = data.with_columns(pl.col("date").dt.strftime("%Y-%m-%d").alias("date_as_string"))
## Simple Moving Average
for ave in moving_averages:
    ave_name = "MA-" + str(ave)
    data = data.with_columns(
        pl.col("close").rolling_mean(window_size=ave).alias(ave_name)
    )
for ema in emas:
    ema_name = "EMA-" + str(ema)
    data = data.with_columns(
        pl.col("close")
        .ewm_mean(
            span=ema,
            min_samples=ema,
            adjust=False,
        )
        .alias(ema_name)
    )

MA_colors = ["blue", "orange", "red", "violet"]
base = alt.Chart(data).encode(
    x=alt.X(
        "date_as_string:O",
        title="Date",
        # timeUnit="yearmonthdate",
        axis=alt.Axis(grid=False, labelAngle=-45),
    ),
)
# Shadows
rule = base.mark_rule().encode(
    y=alt.Y(
        "low:Q",
        title="Price",
        scale=alt.Scale(zero=False),
    ),
    y2=alt.Y2("high:Q"),
    color=alt.condition(
        "datum.open <= datum.close", alt.value("#23DE0E"), alt.value("#f6102b")
    ),
)
# Real body
bar = (
    base.mark_bar()
    .encode(
        y=alt.Y("open:Q"),
        y2=alt.Y2("close:Q"),
        color=alt.condition(
            "datum.open <= datum.close", alt.value("#23DE0E"), alt.value("#f6102b")
        ),
        tooltip=["date:T", "open", "high", "low", "close"],
    )
    .properties(width=600, height=400, title=f"Candlestick for {ticker_name}")
)

candlestick = rule + bar

# Simple Moving Average
color_count = 0
for ave in moving_averages:
    ave_name = "MA-" + str(ave)
    sma = base.mark_line(color=MA_colors[color_count]).encode(
        y=alt.Y(ave_name + ":Q"),
        tooltip=["date", ave_name + ":Q"],
    )
    color_count += 1
    candlestick = candlestick + sma

# Exponential Moving Average
color_count = 0
for ema in emas:
    ema_name = "EMA-" + str(ema)
    ema = base.mark_line(color=MA_colors[color_count], strokeDash=[5, 5]).encode(
        y=alt.Y(ema_name + ":Q"),
        tooltip=["date", ema_name + ":Q"],
    )
    color_count += 1
    candlestick = candlestick + ema


volume = (
    alt.Chart(data)
    .mark_bar(color="dodgerblue")
    .encode(
        x=alt.X(
            "date_as_string:O",
            title="Date",
            axis=alt.Axis(grid=False, labelAngle=-45),
        ),
        y=alt.Y("volume"),
        tooltip=["date:T", "volume"],
    )
    .properties(width=600, height=100, title="Volume")
)
chart = candlestick & volume

st.altair_chart(chart)
