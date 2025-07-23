from datetime import date, datetime

import altair as alt
import polars as pl
import polars_talib as plta
from securities_load.securities.polar_table_functions import (
    retrieve_exchange_ids_using_country_alpha_3,
    retrieve_ohlcv_using_ticker_id_and_dates,
    retrieve_ticker_types,
    retrieve_tickers_using_exchanges_and_ticker_types,
    retrieve_unique_country_alpha_3_from_exchanges,
)

import streamlit as st

st.set_page_config(
    page_title="Screener",
    layout="wide",
)

st.title("Screener")

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
        default=ticker_type_codes[7],
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
