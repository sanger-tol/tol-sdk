from tol.core import DataSourceFilter
from tol.sources.portal import portal

src = portal()

f = DataSourceFilter(
    and_={}
)

obj = src.get_one('species', '9606')

print(obj)