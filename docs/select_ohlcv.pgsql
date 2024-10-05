select t.ticker, e.code, o.date, o.close, o.volume
from securities.ticker t
left join securities.exchange e
on t.exchange_id = e.id
left join securities.ohlcv o
on t.id = o.ticker_id
where e.code = 'XASX'
and t.ticker = 'BHP'
