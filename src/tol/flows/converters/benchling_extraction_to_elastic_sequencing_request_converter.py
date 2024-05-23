# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class BenchlingExtractionToElasticSequencingRequestConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object.sts_id is not None:
            ret = self._data_object_factory(
                'sequencing_request',
                data_object.id,
                attributes={
                    'extraction': {'id': data_object.id},
                    'sample': {'id': data_object.sts_id},
                    'species': {'id': data_object.taxon_id},
                    'specimen': {'id': data_object.specimen_id},
                    'tolid': {'id': data_object.programme_id},
                    'tissue_prep': {'id': data_object.eln_tissue_prep_id},
                    'sequencing_platform': 'pacbio'
                })
            yield ret
