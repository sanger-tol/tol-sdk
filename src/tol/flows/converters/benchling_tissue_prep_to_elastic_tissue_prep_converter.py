# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class BenchlingTissuePrepToElasticTissuePrepConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        ret = self._data_object_factory(
            'tissue_prep',
            data_object.eln_tissue_prep_id,
            attributes={
                **{k: v
                   for k, v in data_object.attributes.items()
                   if k not in ['eln_tissue_prep_id',
                                'sts_id',
                                'taxon_id',
                                'programme_id']}
            },
            to_one={
                'sample': self._data_object_factory(
                    'sample',
                    data_object.sts_id
                ) if data_object.sts_id is not None else None,
                'species': self._data_object_factory(
                    'species',
                    data_object.taxon_id
                ) if data_object.taxon_id is not None else None,
                'tolid': self._data_object_factory(
                    'tolid',
                    data_object.programme_id
                ) if data_object.programme_id is not None else None,
            }
        )
        return iter([ret])
