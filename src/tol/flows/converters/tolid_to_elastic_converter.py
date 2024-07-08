# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolidToElasticConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        ret = self._data_object_factory(
            'tolid',
            data_object.id,
            attributes={
                'specimen_id': data_object.specimen_id,
                'created_at': data_object.created_at,
            },
            to_one={
                'species': self._data_object_factory(
                    'species',
                    data_object.species.id,
                    attributes={
                        'tolid_name': data_object.species.name,
                        'requested_tolid': data_object.species.requested_tolid
                    }
                )
            }
        )
        yield ret
