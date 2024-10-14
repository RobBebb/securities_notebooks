import datetime as dt

from dotenv import load_dotenv
from securities_load.securities.postgresql_database_functions import sqlalchemy_engine
from securities_load.securities.securities_table_functions import (
    retrieve_ohlcv_from_to,
    retrieve_ohlcv_last_n_days,
)

from backtesting import Backtest, Strategy

# from backtesting.lib import crossover
# from backtesting.test import GOOG, SMA


# class SmaCross(Strategy):
#     # Define the two MA lags as *class variables*
#     # for later optimization
#     n1 = 10
#     n2 = 20

#     def init(self):
#         price = self.data.Close
#         self.ma1 = self.I(SMA, price, self.n1)
#         self.ma2 = self.I(SMA, price, self.n2)

# def next(self):
#     if crossover(self.ma1, self.ma2):
#         self.position.close()
#         self.buy()
#     elif crossover(self.ma2, self.ma1):
#         self.position.close()
#         self.sell()


load_dotenv()
engine = sqlalchemy_engine()
exchange_code = "XNAS"
ticker = "GOOG"
num_of_years = 6
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
# df = retrieve_ohlcv_last_n_days(
#     engine,
#     exchange_code=exchange_code,
#     ticker=ticker,
#     days=200,
# )
print(df.info())
print(df.head(3))
print(df.tail(3))
# df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
# print(df.info())

# bt = Backtest(df, SmaCross, commission=0.002, exclusive_orders=True)
# stats = bt.run()
# stats = bt.optimize(
#     n1=range(5, 30, 5),
#     n2=range(10, 70, 5),
#     maximize="Equity Final [$]",
#     constraint=lambda param: param.n1 < param.n2,
# )
# print(stats)

# print(stats._strategy)

# print(
#     stats["_equity_curve"]
# )  # Contains equity/drawdown curves. DrawdownDuration is only defined at ends of DD periods.

# print(stats["_trades"])  # Contains individual trade data)
# bt.plot()
# bt.plot(plot_volume=False, plot_pl=False)
