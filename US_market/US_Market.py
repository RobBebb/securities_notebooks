from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    retrieve_close_using_currency_tickers_dates,
    retrieve_tickers_using_watchlist_code,
    retrieve_watchlists_using_watchlist_type,
)

import streamlit as st

st.set_page_config(
    page_title="US Market Overview",
    layout="wide",
    # page_icon="👋",
)

st.title("US Market Overview")

st.sidebar.success("Select a type of analysis above.")

watchlist_data = retrieve_watchlists_using_watchlist_type("Dashboard")
watchlist_ids = [x[0] for x in watchlist_data]
watchlist_codes = [x[1] for x in watchlist_data]
watchlist_description = [x[2] for x in watchlist_data]

col1, col2 = st.columns([0.4, 0.6])

with col1:
    watchlist = st.pills(
        "Select a watchlist to get symbols:",
        watchlist_codes,
        selection_mode="single",
        default=watchlist_codes[1],
    )

if watchlist:
    ticker_data = retrieve_tickers_using_watchlist_code(watchlist)
    ticker_ids = [x[0] for x in ticker_data]
    ticker_codes = [x[1] for x in ticker_data]
    ticker_names = [x[2] for x in ticker_data]

with col2:
    ticker_code = st.pills(
        "Select a ticker to chart:",
        ticker_codes,
        selection_mode="single",
        default=ticker_codes[0],
    )

if ticker_code:
    ticker_index = ticker_codes.index(ticker_code)
    ticker_name = ticker_names[ticker_index]

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


@st.cache_data
def load_data(tickers, start, end, moving_averages):
    data = retrieve_close_using_currency_tickers_dates("USD", tickers, start, end)

    for ave in moving_averages:
        ave_num = int(ave)
        data = data.with_columns(
            pl.col("close")
            .rolling_mean(window_size=ave_num)
            .over("ticker")
            .alias("MA-" + ave)
        )
    return data


data = load_data(ticker_codes, start, end, moving_averages)


if ticker_code:
    filtered_data = data.filter(pl.col("ticker") == ticker_code)
    filtered_data = filtered_data.drop("ticker")
    long_data = filtered_data.unpivot(
        index="date",
        variable_name="type",
        value_name="value",
    )

    line_chart = (
        alt.Chart(long_data)
        .mark_line(strokeWidth=1.5)
        .encode(
            x=alt.X(
                "date:T",
                title="",
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
                "value:Q",
                title="Price",
                scale=alt.Scale(zero=False),
                axis=alt.Axis(
                    format="$.2f",
                    tickColor="#09080B",
                    domainColor="#09080B",
                    gridColor="#9DCDF8",
                    grid=True,
                    labelFontSize=10,
                    titleFontSize=12,
                ),
            ),
            color="type:N",
            tooltip=["date:T", "value:Q"],
        )
    ).properties(
        title={
            "text": f"Stock Price Analysis for {ticker_code} - {ticker_name}",
            "subtitle": ["Comparison of multiple simple moving averages"],
            "fontSize": 16,
        },
        width=600,
        height=500,
    )
    st.altair_chart(line_chart)
