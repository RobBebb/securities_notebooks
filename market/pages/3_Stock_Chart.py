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
    page_title="Stock Chart",
    layout="wide",
)

st.title("Stock Chart")

countries = retrieve_unique_country_alpha_3_from_exchanges()
country_codes = countries["country_alpha_3"].to_list()
ticker_types = retrieve_ticker_types()
ticker_type_ids = ticker_types["id"].to_list()
ticker_type_codes = ticker_types["code"].to_list()

row1col1, row1col2, row1col3, row1col4 = st.columns([0.25, 0.3, 0.2, 0.25], border=True)

with row1col1:
    st.text("Select a country to get symbols:")
    country = st.pills(
        "Select a country to get symbols:",
        country_codes,
        selection_mode="single",
        default=country_codes[5],
        label_visibility="collapsed",
    )

with row1col2:
    st.text("Select a ticker type to get symbols:")
    ticker_type = st.pills(
        "Select a ticker type to get symbols:",
        ticker_type_codes,
        selection_mode="single",
        default=ticker_type_codes[7],
        label_visibility="collapsed",
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

with row1col3:
    st.text("Select a symbol:")
    ticker = st.selectbox(
        "Select a symbol:",
        ticker_symbols,
        label_visibility="collapsed",
    )
    if ticker:
        ticker_index = ticker_symbols.index(ticker)
        ticker_id = ticker_ids[ticker_index]
        ticker_name = ticker_names[ticker_index]

today = datetime.now()
last_year = date(today.year - 1, 1, 1)
min_date = date(today.year - 5, 1, 1)
max_date = today

with row1col4:
    st.text("Select dates for analysis:")
    selected_dates = st.date_input(
        "Select dates for analysis:",
        (last_year, today),
        min_date,
        max_date,
        format="YYYY-MM-DD",
        label_visibility="collapsed",
    )

if selected_dates and len(selected_dates) == 1:
    start = selected_dates[0].strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

elif selected_dates and len(selected_dates) == 2:
    start = selected_dates[0].strftime("%Y-%m-%d")
    end = selected_dates[1].strftime("%Y-%m-%d")
else:
    st.write("No date selected.")

smas = []

row2col1, row2col2, row2col3 = st.columns([0.375, 0.375, 0.25], border=True)

with row2col1:
    st.text("Specify periods for simple moving averages. Displays solid.")
    row2col1a, row2col1b, row2col1c = st.columns([0.33, 0.33, 0.34])
    with row2col1a:
        sma1 = st.number_input(":blue[SMA 1]", value=None, step=1, key="sma1")
        if sma1:
            smas.append(sma1)
    with row2col1b:
        sma2 = st.number_input(":orange[SMA 2]", value=None, step=1, key="sma2")
        if sma2:
            smas.append(sma2)
    with row2col1c:
        sma3 = st.number_input(":red[SMA 3]", value=None, step=1, key="sma3")
        if sma3:
            smas.append(sma3)

emas = []

with row2col2:
    st.text("Specify periods for exponential moving averages. Displays dashed.")
    row2col2a, rowcol2b, row2col2c = st.columns([0.33, 0.33, 0.34])
    with row2col2a:
        ema1 = st.number_input(":blue[EMA 1]", value=None, step=1, key="ema1")
        if ema1:
            emas.append(ema1)
    with rowcol2b:
        ema2 = st.number_input(":orange[EMA 2]", value=None, step=1, key="ema2")
        if ema2:
            emas.append(ema2)
    with row2col2c:
        ema3 = st.number_input(":red[EMA 3]", value=None, step=1, key="ema3")
        if ema3:
            emas.append(ema3)

vmas = []

with row2col3:
    st.text("Specify periods for volume moving averages.")
    row2col3a, row2col3b = st.columns([0.5, 0.5])
    with row2col3a:
        vma1 = st.number_input(":blue[VMA 1]", value=None, step=1, key="vma1")
        if vma1:
            vmas.append(vma1)
    with row2col3b:
        vma2 = st.number_input(":orange[VMA 2]", value=None, step=1, key="vma2")
        if vma2:
            vmas.append(vma2)

row3col1, row3col2 = st.columns([0.5, 0.5], border=True)

with row3col1:
    st.write("Select the indicators to show.")
    row3col1a, row3col1b, row3col1c, row3col1d = st.columns([0.25, 0.25, 0.25, 0.25])
    with row3col1a:
        show_macd = st.toggle("MACD?", value=False)
    with row3col1b:
        show_rsi = st.toggle("RSI?", value=False)

with row3col2:
    st.write("Select candlestick patterns to show.")
    row3col2a, row3col2b, row3col2d, row3col2d = st.columns([0.25, 0.25, 0.25, 0.25])
    with row3col2a:
        show_hammer = st.toggle("Hammer?", value=False)
    with row3col2b:
        show_2_crows = st.toggle("2 Crows?", value=False)


@st.cache_data
def load_data(ticker_id, start, end):
    data = retrieve_ohlcv_using_ticker_id_and_dates(ticker_id, start, end)

    return data


data = load_data(ticker_id, start, end)

last_date = data[-1, "date"]
last_close = data[-1, "close"]
last_open = data[-1, "open"]
last_high = data[-1, "high"]
last_low = data[-1, "low"]
last_volume = data[-1, "volume"]
change = data[-1, "close"] - data[-2, "close"]
percent_change = (change / data[-2, "close"]) * 100

data = (
    data.with_columns(
        pl.col("date").dt.strftime("%Y-%m-%d").alias("date_as_string"),
        *[plta.sma(pl.col("close"), timeperiod=i).alias(f"sma{i:03d}") for i in smas],
        *[plta.ema(pl.col("close"), timeperiod=i).alias(f"ema{i:03d}") for i in emas],
        plta.macd(fastperiod=10, slowperiod=20, signalperiod=5).alias("macdind"),
        plta.rsi().alias("rsi"),
        plta.ht_dcperiod().alias("ht_dcp"),
        plta.aroon().alias("aroon"),
        plta.wclprice().alias("wclprice"),
        plta.stoch(
            pl.col("high"),
            pl.col("low"),
            pl.col("close"),
            fastk_period=14,
            slowk_period=7,
            slowd_period=7,
        ).alias("stoch"),
        plta.cdl2crows().alias("cdl2crows"),
        plta.cdlhammer().alias("cdlhammer"),
        *[
            pl.col("volume").rolling_mean(window_size=i).alias(f"vma{i:03d}")
            for i in vmas
        ],
    )
    .with_columns(
        pl.col("macdind").struct.field("macd"),
        pl.col("macdind").struct.field("macdsignal"),
        pl.col("macdind").struct.field("macdhist"),
        pl.col("aroon").struct.field("aroondown"),
        pl.col("aroon").struct.field("aroonup"),
        pl.col("stoch").struct.field("slowk"),
        pl.col("stoch").struct.field("slowd"),
    )
    .select(pl.exclude(["macdind", "aroon", "stoch"]))
)

if show_hammer:
    data = data.with_columns(
        pl.when(pl.col("cdlhammer") == 100.0)
        .then(pl.col("wclprice") * 1.025)
        .when(pl.col("cdlhammer") == -100.0)
        .then(pl.col("wclprice") * 0.975)
        .otherwise(None)
        .alias("hammer")
    )

if show_2_crows:
    data = data.with_columns(
        pl.when(pl.col("cdl2crows") == 100.0)
        .then(pl.col("wclprice") * 1.025)
        .when(pl.col("cdl2crows") == -100.0)
        .then(pl.col("wclprice") * 0.975)
        .otherwise(None)
        .alias("crows")
    )

# Do not use interactive charts as it messes up the moving averages

charts = []

MA_colors = ["blue", "orange", "violet"]
base = alt.Chart(data).encode(
    x=alt.X(
        "date_as_string:O",
        title="",
        # timeUnit="yearmonthdate",
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
            labels=False,
        ),
    ),
)
# Shadows
rule = base.mark_rule().encode(
    y=alt.Y(
        "low:Q",
        title="Price",
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
    .properties(
        width=600,
        height=400,
        title={
            "text": f"Candlestick for {ticker_name}",
            "subtitle": [
                f"Date: {last_date}, Close: {last_close:.2f}, Change: {change:.2f} ({percent_change:.2f}%) Volume: {last_volume}",
            ],
            "fontSize": 18,
            "subtitleFontSize": 14,
        },
    )
)

candlestick = rule + bar

# Simple Moving Average
color_count = 0
for i in smas:
    ave_name = f"sma{i:03d}"
    sma = base.mark_line(color=MA_colors[color_count]).encode(
        y=alt.Y(ave_name + ":Q"),
        tooltip=["date", ave_name + ":Q"],
    )
    color_count += 1
    candlestick = candlestick + sma

# Exponential Moving Average
color_count = 0
for i in emas:
    ema_name = f"ema{i:03d}"
    ema = base.mark_line(color=MA_colors[color_count], strokeDash=[5, 5]).encode(
        y=alt.Y(ema_name + ":Q"),
        tooltip=["date", ema_name + ":Q"],
    )
    color_count += 1
    candlestick = candlestick + ema

if show_hammer:
    hammer = base.mark_point(shape="arrow", angle=180, size=100).encode(
        y=alt.Y("hammer:Q"), color=alt.value("#000000")
    )
    candlestick = candlestick + hammer

    hammer_text = base.mark_text(align="left", baseline="bottom", text="Hammer").encode(
        y=alt.Y("hammer:Q"),
    )
    candlestick = candlestick + hammer_text

if show_2_crows:
    crows = base.mark_point(shape="arrow", angle=180, size=100).encode(
        y=alt.Y("crows:Q"), color=alt.value("#000000")
    )
    candlestick = candlestick + crows

    crows_text = base.mark_text(align="left", baseline="bottom", text="Hammer").encode(
        y=alt.Y("crows:Q"),
    )
    candlestick = (candlestick + crows_text).interactive()

charts.append(candlestick)

volume_base = alt.Chart(data).encode(
    x=alt.X(
        "date_as_string:O",
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
)
volume = (
    volume_base.mark_bar(color="dodgerblue")
    .encode(
        y=alt.Y(
            "volume:Q",
            title="Volume",
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
        tooltip=["date:T", "volume:Q"],
    )
    .properties(width=1300, height=200)
)


color_count = 0
for i in vmas:
    vma_name = f"vma{i:03d}"
    vma = base.mark_line(color=MA_colors[color_count]).encode(
        y=alt.Y(vma_name + ":Q"),
        tooltip=["date", vma_name + ":Q"],
    )
    color_count += 1
    volume = volume + vma


if show_macd:
    macd = (
        alt.Chart(data)
        .encode(
            x=alt.X(
                "date_as_string:O",
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
                    labels=False,
                ),
            )
        )
        .properties(width=1300, height=100, title="")
    )

    macd_line = macd.mark_line(color="dodgerblue", strokeWidth=1).encode(
        y=alt.Y(
            "macd:Q",
            title="MACD & Signal",
            axis=alt.Axis(
                tickColor="#000000",
                domainColor="#D0D3D3",
                gridColor="#D0D3D3",
                labelColor="#000000",
                titleColor="#000000",
                labelFontSize=12,
                titleFontSize=16,
                grid=False,
                labels=True,
            ),
        ),
        tooltip=["date:T", "macd:Q"],
    )

    signal_line = macd.mark_line(color="darkorange", strokeWidth=1).encode(
        y=alt.Y("macdsignal:Q", title=""), tooltip=["date:T", "macdsignal:Q"]
    )

    macd_lines = (
        alt.layer(
            signal_line,
            macd_line,
        )
        .resolve_scale(x="shared", y="shared")
        .properties(title="", width=1300, height=100)
    )

    histogram = macd.mark_bar(size=3).encode(
        y=alt.Y(
            "macdhist:Q",
            title="MACD Hist",
            axis=alt.Axis(
                # format="f",
                tickColor="#9D9BA1",
                domainColor="#000000",
                gridColor="#D0D3D3",
                labelColor="#000000",
                titleColor="#000000",
                grid=True,
                labelFontSize=12,
                titleFontSize=16,
            ),
        ),
        color=alt.condition(
            alt.datum.macdhist > 0,  # Positive bars
            alt.value("green"),
            alt.value("red"),  # Negative bars
        ),
        tooltip=["date:T", "macdhist:Q", "macd:Q", "macdsignal:Q"],
    )

    macd_chart = (
        alt.layer(
            histogram,
            macd_lines,
        )
        .resolve_scale(x="shared", y="independent")
        .properties(title="", width=1300, height=100)
    )
    charts.append(macd_chart)

if show_rsi:
    # Relative Strength Index (RSI)
    # Create a base chart for RSI
    rsi = (
        alt.Chart(data)
        .encode(
            x=alt.X(
                "date_as_string:O",
                title="",
                axis=alt.Axis(
                    tickColor="#D0D3D3",
                    domainColor="#000000",
                    gridColor="#D0D3D3",
                    labelColor="#000000",
                    titleColor="#000000",
                    labelFontSize=12,
                    titleFontSize=16,
                    grid=False,
                    labelAngle=-45,
                    labels=False,
                ),
            )
        )
        .properties(width=1300, height=100, title="")
    )

    rsi_line = rsi.mark_line(color="dodgerblue", strokeWidth=1).encode(
        y=alt.Y(
            "rsi:Q",
            title="RSI",
            axis=alt.Axis(
                tickColor="#D0D3D3",
                domainColor="#000000",
                gridColor="#D0D3D3",
                labelColor="#000000",
                titleColor="#000000",
                labelFontSize=12,
                titleFontSize=16,
                grid=True,
                labels=True,
            ),
        ),
        tooltip=["date:T", "rsi:Q"],
    )
    yrule_upper = (
        alt.Chart()
        .mark_rule(strokeDash=[2, 2], color="#9219E9")
        .encode(y=alt.datum(70))
    )

    yrule_lower = (
        alt.Chart()
        .mark_rule(strokeDash=[2, 2], color="#9219E9")
        .encode(y=alt.datum(30))
    )

    rsi_fill = rsi.mark_area(color="#9219E9", opacity=0.1).encode(
        y=alt.datum(30), y2=alt.datum(70)
    )

    rsi_chart = rsi_line + yrule_lower + yrule_upper + rsi_fill
    charts.append(rsi_chart)

charts.append(volume)

combined_chart = (
    alt.vconcat(*charts).resolve_scale(x="shared").configure(background="#eaf3fb")
)

st.altair_chart(combined_chart)
