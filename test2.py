from tol.core import DataSourceFilter
from tol.sources.portal import portal

src = portal()
f = DataSourceFilter(
    and_ = {"sts_sample_sts_programme_union":{"eq":{"value":"ToL"}}}
)
objs = src.get_list('species', object_filters=f)
for obj in objs:
    print(obj.attributes)