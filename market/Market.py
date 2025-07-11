from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    retrieve_close_using_ticker_ids_and_dates,
    retrieve_tickers_using_watchlist_code,
    retrieve_unique_country_alpha_3_from_exchanges,
    retrieve_watchlists_using_watchlist_type,
)

import streamlit as st

st.set_page_config(
    page_title="Market Overview",
    layout="wide",
    # page_icon="👋",
)

st.title("Market Overview")

st.sidebar.success("Select a type of analysis above.")

countries = retrieve_unique_country_alpha_3_from_exchanges()
country_codes = countries["country_alpha_3"].to_list()

col1, col2, col3 = st.columns([0.34, 0.33, 0.33])

with col1:
    country = st.pills(
        "Select a country to get watchlists:",
        country_codes,
        selection_mode="single",
        default=country_codes[5],
    )

watchlist_data = retrieve_watchlists_using_watchlist_type("Dashboard")
watchlist_ids = [x[0] for x in watchlist_data]
watchlist_codes = [x[1] for x in watchlist_data]
watchlist_description = [x[2] for x in watchlist_data]

watchlists = []
for code in watchlist_codes:
    if code.split(" ")[0] == country:
        watchlists.append(code)

if len(watchlists) == 0:
    st.warning(
        "No watchlists available for the selected country at the moment. Please select another country."
    )
    st.stop()

with col2:
    watchlist = st.pills(
        "Select a watchlist to get symbols:",
        watchlists,
        selection_mode="single",
        default=watchlists[0],
    )

today = datetime.now()
last_year = date(today.year - 1, 1, 1)
min_date = date(today.year - 5, 1, 1)
max_date = today

with col3:
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
    st.warning("No date selected. Please select a date.")
    st.stop()

if watchlist:
    ticker_data = retrieve_tickers_using_watchlist_code(watchlist)
    ticker_ids = [x[0] for x in ticker_data]
    ticker_codes = [x[1] for x in ticker_data]
    ticker_names = [x[2] for x in ticker_data]

col1a, col2a = st.columns([0.67, 0.33])

with col1a:
    ticker_code = st.pills(
        "Please select a symbol to chart:",
        ticker_codes,
        selection_mode="single",
        default=ticker_codes[0],
    )

if ticker_code:
    ticker_index = ticker_codes.index(ticker_code)
    ticker_name = ticker_names[ticker_index]


averages = ["5", "10", "20", "50", "200"]

with col2a:
    moving_averages = st.pills(
        "Select one or more moving average periods to display:",
        averages,
        selection_mode="multi",
        default=averages[3:5],
    )


@st.cache_data
def load_data(tickers, start, end, moving_averages):
    data = retrieve_close_using_ticker_ids_and_dates(ticker_ids, start, end)

    for ave in moving_averages:
        ave_num = int(ave)
        data = data.with_columns(
            pl.col("close")
            .rolling_mean(window_size=ave_num)
            .over("ticker")
            .alias("MA-" + ave)
        )
    return data


data = load_data(ticker_ids, start, end, moving_averages)


if ticker_code:
    filtered_data = data.filter(pl.col("ticker") == ticker_code)
    filtered_data = filtered_data.drop("ticker", "id")
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
