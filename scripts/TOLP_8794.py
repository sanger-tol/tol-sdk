# benchmarks the performance of targeted re-summarisation
# against various summary objects with a real datum

import cProfile

from tol.sources.elastic import elastic
from tol.sources.portaldb import portaldb


eds = elastic()
eds.attribute_metadata

summary = [
    s for s in portaldb().get_list('summary')
    # ID of pathlogically slow summary object
    if s.id == '39'
][0]

print(str(summary), summary.attributes)


def main() -> None:
    eds.resummarise_by_ids(
        [summary],
        source_object_type='sequencing_request',
        # has a `benchling_extraction`
        source_object_ids=['5976STDY13130848'],
    )


cProfile.run('main()')
