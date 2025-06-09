from tol.sources.elastic import elastic
from tol.sources.portaldb import portaldb


eds = elastic()

summaries = list(
    portaldb().get_list('summary')
)

eds.resummarise_by_ids(
    summaries,
    source_object_type='sequencing_request',
    # has a `benchling_extraction`
    source_object_ids=['5976STDY13130848'],
)
