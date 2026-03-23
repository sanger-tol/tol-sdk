# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolidSpecimenToElasticTolidConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        ret = self._data_object_factory(
            'tolid',
            data_object.id,
            attributes={
                'created_at': data_object.created_at,
                'requested_taxonomy_id': data_object.requested_taxonomy_id,
                'legacy_name': data_object.legacy_name,
            },
            to_one={
                'species': self._data_object_factory(
                    'species',
                    data_object.species.id
                ),
                'specimen': self._data_object_factory(
                    'specimen',
                    data_object.specimen_id
                )
            }
        )
        yield ret
