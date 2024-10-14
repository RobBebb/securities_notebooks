select t.id, t.ticker, e.code
from securities.ticker t
left join securities.exchange e
on t.exchange_id = e.id
where t.ticker = 'AMAT'