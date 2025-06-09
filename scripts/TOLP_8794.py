from tol.sources.elastic import elastic
from tol.sources.portaldb import portaldb


eds = elastic()

summaries = list(
    portaldb().get_list('summary')
)

eds.resummarise_by_ids(
    summaries,
    source_object_type='sequencing_request',
    source_object_ids=['2021acTZ11512777'],
)
