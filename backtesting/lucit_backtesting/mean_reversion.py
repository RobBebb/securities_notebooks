import pandas as pd
import yfinance as yf
from talib import abstract

from backtesting import Backtest, Strategy

sma = abstract.Function("sma")

# Obtain OHLV data for HE
# Obtain OHLV data for HE
he = yf.download("HE", start="2024-08-16", interval="15m")[
    ["Open", "High", "Low", "Close", "Volume"]
]


def std_3(arr, n):
    return pd.Series(arr).rolling(n).std() * 3


class MeanReversion(Strategy):
    roll = 50

    def init(self):
        self.he = self.data.Close

        self.he_mean = self.I(sma, self.he, self.roll)
        self.he_std = self.I(std_3, self.he, self.roll)
        self.he_upper = self.he_mean + self.he_std
        self.he_lower = self.he_mean - self.he_std

        self.he_close = self.I(sma, self.he, 2)

    def next(self):

        if self.he_close < self.he_lower:
            self.buy(
                tp=self.he_mean,  # type: ignore
            )

        if self.he_close > self.he_upper:
            self.sell(
                tp=self.he_mean,  # type: ignore
            )


bt = Backtest(he, MeanReversion, cash=10000, commission=0.002)
stats = bt.run()
bt.plot()
print(stats)
