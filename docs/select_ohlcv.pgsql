select t.ticker, e.code, count(o.date)
from securities.ticker t
left join securities.exchange e
on t.exchange_id = e.id
left join securities.ohlcv o
on t.id = o.ticker_id
where e.code = 'XNYS'
and t.ticker = 'CSX'
group by 1,2
