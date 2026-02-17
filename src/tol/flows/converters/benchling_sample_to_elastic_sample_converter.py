# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class BenchlingSampleToElasticSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object.id is not None:
            ret = self._data_object_factory(
                'sample',
                str(data_object.id),
                attributes={
                    f'{k}': v
                    for k, v in data_object.attributes.items()
                    if k not in ['taxon_id', 'specimen_id', 'programme_id']
                },
                to_one={
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
                    ) if data_object.programme_id is not None else None
                }
            )
            yield ret
