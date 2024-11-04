import matplotlib.pyplot as plt
import seaborn as sns
from backtesting.lib import crossover, plot_heatmaps
from backtesting.test import GOOG, SMA
from skopt.plots import plot_evaluations, plot_objective

from backtesting import Backtest, Strategy


class Sma4Cross(Strategy):
    n1 = 50
    n2 = 100
    n_enter = 20
    n_exit = 10

    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
        self.sma_enter = self.I(SMA, self.data.Close, self.n_enter)
        self.sma_exit = self.I(SMA, self.data.Close, self.n_exit)

    def next(self):

        if not self.position:

            # On upwards trend, if price closes above
            # "entry" MA, go long

            # Here, even though the operands are arrays, this
            # works by implicitly comparing the two last values
            if self.sma1 > self.sma2:
                if crossover(self.data.Close, self.sma_enter):
                    self.buy()

            # On downwards trend, if price closes below
            # "entry" MA, go short

            else:
                if crossover(self.sma_enter, self.data.Close):
                    self.sell()

        # But if we already hold a position and the price
        # closes back below (above) "exit" MA, close the position

        else:
            if (
                self.position.is_long
                and crossover(self.sma_exit, self.data.Close)
                or self.position.is_short
                and crossover(self.data.Close, self.sma_exit)
            ):

                self.position.close()


backtest = Backtest(GOOG, Sma4Cross, commission=0.002)

# stats, heatmap = backtest.optimize(
#     n1=range(10, 110, 10),
#     n2=range(20, 210, 20),
#     n_enter=range(15, 35, 5),
#     n_exit=range(10, 25, 5),
#     constraint=lambda p: p.n_exit < p.n_enter < p.n1 < p.n2,
#     maximize="Equity Final [$]",
#     max_tries=200,
#     random_state=0,
#     return_heatmap=True,
# )

# print(heatmap.sort_values().iloc[-3:])

# hm = heatmap.groupby(["n1", "n2"]).mean().unstack()
# print(hm)

# sns.heatmap(hm[::-1], cmap="viridis")

# plt.show()

# hm2 = plot_heatmaps(heatmap, agg="mean")
# plt.show()

stats_skopt, heatmap, optimize_result = backtest.optimize(
    n1=[10, 100],  # Note: For method="skopt", we
    n2=[20, 200],  # only need interval end-points
    n_enter=[10, 40],
    n_exit=[10, 30],
    constraint=lambda p: p.n_exit < p.n_enter < p.n1 < p.n2,
    maximize="Equity Final [$]",
    method="skopt",
    max_tries=200,
    random_state=0,
    return_heatmap=True,
    return_optimization=True,
)

print(heatmap.sort_values().iloc[-3:])

# _ = plot_objective(optimize_result, n_points=10)

# plt.show()

_ = plot_evaluations(optimize_result, bins=10)
plt.show()
