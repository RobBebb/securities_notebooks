from datetime import date, datetime, timedelta, timezone

import pytest


@pytest.fixture
def options():
    # UTC
    tz = timezone(timedelta(hours=0))
    options = {
        "A250718C00130000_buy": {
            "expiry_date": date(2025, 7, 18),  # type: ignore
            "ticker": "A250718C00130000",
            "strike": 130.0,
            "bid": 0.1,
            "ask": 0.25,
            "mid": 0.175,
            "volume": 2,
            "open_interest": 123,
            "implied_volatility": 0.280281,
            "id": 1930231,
            "call_put": "C",
            "date": date(2025, 7, 11),  # type: ignore
            "last_trade_date": datetime(2025, 7, 10, 19, 48, 55, 0000, tzinfo=tz),
            "last_price": 0.2,
            "change": -0.15,
            "percent_change": -42.85714,
            "in_the_money": "F",
            "buy": True,
            "sell": False,
        },
        "A250718C00125000_sell": {
            "expiry_date": date(2025, 7, 18),
            "ticker": "A250718C00125000",
            "strike": 125.0,
            "bid": 1.05,
            "ask": 1.4,
            "mid": 1.225,
            "volume": 5,
            "open_interest": 480,
            "implied_volatility": 0.3,
            "id": 5,
            "call_put": "C",
            "date": date(2025, 7, 11),  # type: ignore
            "last_trade_date": datetime(2025, 7, 11, 13, 30, 3).timestamp(),
            "last_price": 1.24,
            "change": -0.71,
            "percent_change": -36.4,
            "in_the_money": "F",
            "buy": False,
            "sell": True,
        },
        "A250718P00115000_buy": {
            "expiry_date": date(2025, 7, 18),  # type: ignore
            "ticker": "A250718P00115000",
            "strike": 115.0,
            "bid": 0.1,
            "ask": 0.4,
            "mid": 0.25,
            "volume": 6,
            "open_interest": 567,
            "implied_volatility": 0.395026,
            "id": 1930243,
            "call_put": "P",
            "date": date(2025, 7, 11),  # type: ignore
            "last_trade_date": datetime(2025, 7, 10, 17, 48, 23, 0000, tzinfo=tz),
            "last_price": 0.22,
            "change": 0.0,
            "percent_change": 0.0,
            "in_the_money": "F",
            "buy": True,
            "sell": False,
        },
        "A250718P00120000_sell": {
            "expiry_date": date(2025, 7, 18),  # type: ignore
            "ticker": "A250718P00120000",
            "strike": 120.0,
            "bid": 0.6,
            "ask": 0.85,
            "mid": 0.725,
            "volume": 9,
            "open_interest": 358,
            "implied_volatility": 0.291511,
            "id": 1930244,
            "call_put": "P",
            "date": date(2025, 7, 11),  # type: ignore
            "last_trade_date": datetime(2025, 7, 11, 19, 27, 56, 0000, tzinfo=tz),
            "last_price": 0.7,
            "change": -0.1,
            "percent_change": -12.500002,
            "in_the_money": "F",
            "buy": False,
            "sell": True,
        },
    }
    return options
