from datetime import date, datetime

import altair as alt
import polars as pl
from securities_load.securities.polar_table_functions import (
    retrieve_close_using_currency_tickers_dates,
    retrieve_close_using_ticker_ids_and_dates,
    retrieve_tickers_using_watchlist_code,
    retrieve_unique_country_alpha_3_from_exchanges,
)

import streamlit as st

st.set_page_config(
    page_title="Sector Comparision",
    layout="wide",
    # page_icon="👋",
)

st.title("Sector Comparison")

st.markdown("Select multiple sectors to compare how they have performed.")
st.markdown("""All symbols are rebased to 100 on the first date selected.
        This allows an easy comparison of how they have performed.""")

countries = retrieve_unique_country_alpha_3_from_exchanges()
country_codes = countries["country_alpha_3"].to_list()

col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.4, 0.2])

with col1:
    country = st.pills(
        "Select a country for comparison:",
        country_codes,
        selection_mode="single",
        default=country_codes[5],
    )

if country is None:
    st.warning("Please select a country.")
    st.stop()

watchlist = country + " Sector Overview"

try:
    ticker_data = retrieve_tickers_using_watchlist_code(watchlist)
except ValueError:
    st.warning(
        "No watchlist available for the selected country at the moment. Please select another country."
    )
    st.stop()
ticker_ids = [x[0] for x in ticker_data]
ticker_codes = [x[1] for x in ticker_data]
ticker_names = [x[2] for x in ticker_data]

default_selected_tickers = ticker_codes[0]

today = datetime.now()
last_year = date(today.year - 1, 1, 1)
min_date = date(today.year - 5, 1, 1)
max_date = today

with col2:
    selected_dates = st.date_input(
        "Select dates for analysis:",
        (last_year, today),
        min_date,
        max_date,
        format="YYYY-MM-DD",
    )

with col4:
    select_all = st.toggle("Select all tickers", value=False)

if select_all:
    default_selected_tickers = ticker_codes

with col3:
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
    data = retrieve_close_using_ticker_ids_and_dates(ticker_ids, start, end)

    return data


data = load_data(ticker_codes, start, end)

rebased_data = data.with_columns(
    rebase_close=pl.col("close") / pl.first("close").over("ticker") * 100
)

if selected_ticker_codes:
    filtered_data = rebased_data.filter(pl.col("ticker").is_in(selected_ticker_codes))
    filtered_data = filtered_data.drop("close", "id")

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
            "text": "Comparison of multiple sectors",
            "subtitle": [f"All close prices have been rebased to 100 on {start}"],
            "fontSize": 16,
        },
        width=600,
        height=500,
        background="#eaf3fb",
    )
    st.altair_chart(line_chart)

st.dataframe(symbols_df, width=450, row_height=25)
