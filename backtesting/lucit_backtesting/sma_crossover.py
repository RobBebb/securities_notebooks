from backtesting.lib import crossover
from backtesting.test import GOOG, SMA

from backtesting import Backtest, Strategy


class SmaCross(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(SMA, price, 10)
        self.ma2 = self.I(SMA, price, 20)

    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.sell()


bt = Backtest(GOOG, SmaCross, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
bt.plot()
