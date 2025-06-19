from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    retrieve_close_using_currency_tickers_dates,
    retrieve_tickers_using_watchlist_code,
)

import streamlit as st

st.set_page_config(
    page_title="US Sector Comparision",
    layout="wide",
    # page_icon="👋",
)

st.title("US Sector Comparison")

st.markdown("Select multiple sectors to compare how they have performed.")
st.markdown("""All symbols are rebased to 100 on the first date selected.
        This allows an easy comparison of how they have performed.""")

watchlist = "US Sector Overview"
if watchlist:
    ticker_data = retrieve_tickers_using_watchlist_code(watchlist)
    ticker_ids = [x[0] for x in ticker_data]
    ticker_codes = [x[1] for x in ticker_data]
    ticker_names = [x[2] for x in ticker_data]

default_selected_tickers = ticker_codes[0]

today = datetime.now()
last_year = date(today.year - 1, 1, 1)
min_date = date(today.year - 5, 1, 1)
max_date = today

col1, col2, col3 = st.columns([0.23, 0.62, 0.15])

with col1:
    selected_dates = st.date_input(
        "Select dates for analysis:",
        (last_year, today),
        min_date,
        max_date,
        format="YYYY-MM-DD",
    )

with col3:
    select_all = st.toggle("Select all tickers", value=False)

if select_all:
    default_selected_tickers = ticker_codes

with col2:
    selected_ticker_codes = st.pills(
        "Select tickers to chart:",
        ticker_codes,
        selection_mode="multi",
        default=default_selected_tickers,
    )

if selected_dates and len(selected_dates) == 1:
    start = selected_dates[0].strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

elif selected_dates and len(selected_dates) == 2:
    start = selected_dates[0].strftime("%Y-%m-%d")
    end = selected_dates[1].strftime("%Y-%m-%d")
else:
    st.write("No date selected.")

symbols_df = pl.DataFrame({"Symbol": ticker_codes, "Name": ticker_names})


@st.cache_data
def load_data(tickers, start, end):
    data = retrieve_close_using_currency_tickers_dates("USD", tickers, start, end)

    return data


data = load_data(ticker_codes, start, end)

rebased_data = data.with_columns(
    rebase_close=pl.col("close") / pl.first("close").over("ticker") * 100
)

if selected_ticker_codes:
    filtered_data = rebased_data.filter(pl.col("ticker").is_in(selected_ticker_codes))
    filtered_data = filtered_data.drop("close")

    line_chart = (
        alt.Chart(filtered_data)
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
                "rebase_close:Q",
                title="value",
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
            color="ticker:N",
            tooltip=["date:T", "rebase_close:Q"],
        )
    ).properties(
        title={
            "text": "Comparison of multiple sectors",
            "subtitle": [f"All close prices have been rebased to 100 on {start}"],
            "fontSize": 16,
        },
        width=600,
        height=500,
    )
    st.altair_chart(line_chart)

st.dataframe(symbols_df, width=450, row_height=25)
