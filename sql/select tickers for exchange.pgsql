select t.ticker, e.code
from securities.ticker t
left join securities.exchange e
on t.exchange_id = e.id
where e.code = 'XASX'