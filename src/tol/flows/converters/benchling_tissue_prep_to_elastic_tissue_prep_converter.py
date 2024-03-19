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
                'sample': {'id': str(data_object.sts_id)},
                'species': {'id': str(data_object.taxon_id)},
                'tolid': {'id': data_object.programme_id},
                **{k: v
                   for k, v in data_object.attributes.items()
                   if k not in ['eln_tissue_prep_id',
                                'sts_id',
                                'taxon_id',
                                'programme_id']}
            }
        )
        return iter([ret])
