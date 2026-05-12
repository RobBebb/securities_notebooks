import datetime as dt

import pandas as pd
from backtesting.lib import SignalStrategy, TrailingStrategy, crossover
from backtesting.test import GOOG, SMA
from dotenv import load_dotenv
from securities_load.securities.postgresql_database_functions import sqlalchemy_engine
from securities_load.securities.securities_table_functions import (
    retrieve_ohlcv_from_to,
    retrieve_ohlcv_last_n_days,
)

from backtesting import Backtest, Strategy


class SmaCross(SignalStrategy, TrailingStrategy):
    # Define the two MA lags as *class variables*
    # for later optimization
    n1 = 10
    n2 = 25

    def init(self):
        # In init() and in next() it is important to call the
        # super method to properly initialize the parent classes
        super().init()

        # Precompute the two moving averages
        sma1 = self.I(SMA, self.data.Close, self.n1)
        sma2 = self.I(SMA, self.data.Close, self.n2)

        # Where sma1 crosses sma2 upwards. Diff gives us [-1,0, *1*]
        signal = (pd.Series(sma1) > sma2).astype(int).diff().fillna(0)
        signal = signal.replace(-1, 0)  # Upwards/long only

        # Use 95% of available liquidity (at the time) on each order.
        # (Leaving a value of 1. would instead buy a single share.)
        entry_size = signal * 0.95

        # Set order entry sizes using the method provided by
        # `SignalStrategy`. See the docs.
        self.set_signal(entry_size=entry_size)

        # Set trailing stop-loss to 2x ATR using
        # the method provided by `TrailingStrategy`
        self.set_trailing_sl(2)

    # def next(self):
    #     # If sma1 crosses above sma2, close any existing
    #     # short trades, and buy the asset
    #     if crossover(self.sma1, self.sma2):
    #         self.position.close()
    #         self.buy()

    #     # Else, if sma1 crosses below sma2, close any existing
    #     # long trades, and sell the asset
    #     elif crossover(self.sma2, self.sma1):
    #         self.position.close()
    #         self.sell()


load_dotenv()
engine = sqlalchemy_engine()
exchange_code = "XNAS"
ticker = "GOOG"
num_of_years = 10
start_date = dt.datetime.now() - dt.timedelta(int(365.25 * num_of_years))
start_date_str = dt.datetime.strftime(start_date, "%Y-%m-%d")
end_date = dt.datetime.now()
end_date_str = dt.datetime.strftime(end_date, "%Y-%m-%d")
print(start_date)
print(end_date)
df = retrieve_ohlcv_from_to(
    engine,
    exchange_code=exchange_code,
    ticker=ticker,
    start_date=start_date_str,
    end_date=end_date_str,
)
print(df.info())
print(df.head(3))
print(df.tail(3))
df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
print(df.info())

bt = Backtest(df, SmaCross, commission=0.002)
bt.run()
bt.plot()
