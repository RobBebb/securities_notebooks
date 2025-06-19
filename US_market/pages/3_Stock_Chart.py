from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    retrieve_ohlcv_using_ticker_id_and_dates,
)

import streamlit as st

st.set_page_config(
    page_title="Stock Chart",
    layout="wide",
    # page_icon="👋",
)

st.title("Stock Chart")

# watchlist_data = retrieve_watchlists_using_watchlist_type("Dashboard")
# watchlist_ids = [x[0] for x in watchlist_data]
# watchlist_codes = [x[1] for x in watchlist_data]
# watchlist_description = [x[2] for x in watchlist_data]

col1, col2 = st.columns([0.4, 0.6])

# with col1:
#     watchlist = st.pills(
#         "Select a watchlist to get symbols:",
#         watchlist_codes,
#         selection_mode="single",
#         default=watchlist_codes[1],
#     )

# if watchlist:
#     ticker_data = retrieve_tickers_using_watchlist_code(watchlist)
#     ticker_ids = [x[0] for x in ticker_data]
#     ticker_codes = [x[1] for x in ticker_data]
#     ticker_names = [x[2] for x in ticker_data]

# with col2:
#     ticker_code = st.pills(
#         "Select a ticker to chart:",
#         ticker_codes,
#         selection_mode="single",
#         default=ticker_codes[0],
#     )

# if ticker_code:
#     ticker_index = ticker_codes.index(ticker_code)
#     ticker_name = ticker_names[ticker_index]

today = datetime.now()
last_year = date(today.year - 1, 1, 1)
min_date = date(today.year - 5, 1, 1)
max_date = today

with col1:
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

averages = ["5", "10", "20", "50", "200"]

with col2:
    moving_averages = st.pills(
        "Select one or more moving average periods to display:",
        averages,
        selection_mode="multi",
        default=averages[3:5],
    )

ticker_id = 148055
ticker_code = "ZXZX"


@st.cache_data
def load_data(ticker_id, start, end):
    data = retrieve_ohlcv_using_ticker_id_and_dates(ticker_id, start, end)

    return data


data = load_data(ticker_id, start, end)
data = data.with_columns(pl.col("date").dt.strftime("%Y-%m-%d").alias("date_as_string"))
# st.write(data)
## Simple Moving Average
for ave in moving_averages:
    ave_num = int(ave)
    ave_name = "MA-" + ave
    data = data.with_columns(
        pl.col("close").rolling_mean(window_size=ave_num).alias(ave_name)
    )
MA_colors = ["#170c3b", "#fa8d0b", "#7a1d8d", "#e4eb27", "#2de3e6"]
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
    .properties(width=600, height=400, title="Candlestick")
)

candlestick = rule + bar

# sma = base.mark_line(color="purple").encode(
#     y=alt.Y("MA-10:Q"),
#     tooltip=["date:T", "MA-10:Q"],
# )
# candlestick = rule + bar + sma


# Simple Moving Average
color_count = 0
for ave in moving_averages:
    ave_num = int(ave)
    ave_name = "MA-" + ave
    sma = base.mark_line(color=MA_colors[color_count]).encode(
        y=alt.Y(ave_name + ":Q"),
        tooltip=["date", ave_name + ":Q"],
    )
    color_count += 1
    candlestick = candlestick + sma

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
