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
                extraction = self._data_object_factory(
                    'extraction',
                    data_object.extraction_id
                )
            if 'tissue_prep_id' in data_object.attributes:
                tissue_prep = self._data_object_factory(
                    'tissue_prep',
                    data_object.tissue_prep_id
                )
            ret = self._data_object_factory(
                'sequencing_request',
                data_object.sanger_sample_id,
                attributes={
                    **{k: v
                       for k, v in data_object.attributes.items()
                       if k not in ['sanger_sample_id', 'sts_id',
                                    'specimen_id', 'taxon_id', 'extraction_id',
                                    'programme_id', 'tissue_prep_id']}
                },
                to_one={
                    'sample': self._data_object_factory(
                        'sample',
                        data_object.sts_id
                    ) if data_object.sts_id is not None else None,
                    'specimen': self._data_object_factory(
                        'specimen',
                        data_object.specimen_id
                    ) if data_object.specimen_id is not None else None,
                    'species': self._data_object_factory(
                        'species',
                        data_object.taxon_id
                    ) if data_object.taxon_id is not None else None,
                    'tolid': self._data_object_factory(
                        'tolid',
                        data_object.programme_id
                    ) if data_object.programme_id is not None else None,
                    'extraction': extraction,
                    'tissue_prep': tissue_prep,
                })
            yield ret
