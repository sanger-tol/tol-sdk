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
                    'sequencing_platform': 'pacbio'
                },
                to_one={
                    'extraction': self._data_object_factory(
                        'extraction',
                        data_object.id
                    ) if data_object.id is not None else None,
                    'sample': self._data_object_factory(
                        'sample',
                        data_object.sts_id
                    ) if data_object.sts_id is not None else None,
                    'species': self._data_object_factory(
                        'species',
                        data_object.taxon_id
                    ) if data_object.taxon_id is not None else None,
                    'specimen': self._data_object_factory(
                        'specimen',
                        data_object.specimen_id
                    ) if data_object.specimen_id is not None else None,
                    'tolid': self._data_object_factory(
                        'tolid',
                        data_object.programme_id
                    ) if data_object.programme_id is not None else None,
                    'tissue_prep': self._data_object_factory(
                        'tissue_prep',
                        data_object.eln_tissue_prep_id
                    ) if data_object.eln_tissue_prep_id is not None else None,
                }
            )
            yield ret
