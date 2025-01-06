# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class BenchlingSequencingRequestToElasticSequencingRequestConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object.sts_id is not None:
            extraction = None
            tissue_prep = None
            if 'extraction_id' in data_object.attributes:
                extraction = {'id': data_object.extraction_id}
            if 'tissue_prep_id' in data_object.attributes:
                tissue_prep = {'id': data_object.tissue_prep_id}
            ret = self._data_object_factory(
                'sequencing_request',
                data_object.sanger_sample_id,
                attributes={
                    'sample': {'id': str(data_object.sts_id)},
                    'specimen': {'id': str(data_object.specimen_id)},
                    'species': {'id': str(data_object.taxon_id)},
                    'tolid': {'id': data_object.programme_id},
                    'extraction': extraction,
                    'tissue_prep': tissue_prep,
                    **{k: v
                       for k, v in data_object.attributes.items()
                       if k not in ['sanger_sample_id', 'sts_id',
                                    'specimen_id', 'taxon_id', 'extraction_id',
                                    'programme_id', 'tissue_prep_id']}})
            yield ret
