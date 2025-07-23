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
    page_title="US Sector Company Comparison",
    layout="wide",
    # page_icon="👋",
)

st.title("US Sector Company Comparison")

st.markdown("""Select multiple companies to compare how they have performed.
            This is a subset of companies in the sector.""")
st.markdown("""All symbols are rebased to 100 on the first date selected.
        This allows an easy comparison of how they have performed.""")

watchlist_data = retrieve_watchlists_using_watchlist_type("US Sector Samples")
watchlist_ids = [x[0] for x in watchlist_data]
watchlist_codes = [x[1] for x in watchlist_data]
watchlist_description = [x[2] for x in watchlist_data]

col1, col2 = st.columns([0.4, 0.6])

with col1:
    watchlist = st.pills(
        "Select a sector to get symbols:",
        watchlist_codes,
        selection_mode="single",
        default=watchlist_codes[0],
    )

st.write(watchlist)

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
                    tickColor="#000000",
                    domainColor="#D0D3D3",
                    gridColor="#D0D3D3",
                    labelColor="#000000",
                    titleColor="#000000",
                    labelFontSize=12,
                    titleFontSize=16,
                    grid=False,
                    labelAngle=-45,
                    labels=True,
                ),
            ),
            y=alt.Y(
                "rebase_close:Q",
                title="",
                scale=alt.Scale(zero=False),
                axis=alt.Axis(
                    tickColor="#000000",
                    domainColor="#D0D3D3",
                    gridColor="#D0D3D3",
                    labelColor="#000000",
                    titleColor="#000000",
                    labelFontSize=12,
                    titleFontSize=16,
                    grid=True,
                    labels=True,
                ),
            ),
            color="ticker:N",
            tooltip=["date:T", "rebase_close:Q"],
        )
    ).properties(
        title={
            "text": "Comparison of multiple companies",
            "subtitle": [f"All close prices have been rebased to 100 on {start}"],
            "fontSize": 16,
        },
        width=600,
        height=500,
        background="#eaf3fb",
    )
    st.altair_chart(line_chart)

st.dataframe(symbols_df, width=450, row_height=25)
