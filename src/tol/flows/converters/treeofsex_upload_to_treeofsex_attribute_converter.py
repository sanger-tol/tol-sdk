# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TreeofsexUploadToTreeofsexAttributeConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def __init__(self, data_object_factory, user=None):
        super().__init__(data_object_factory)
        self.__sources_seen = set()
        self.__species_seen = set()
        self.__user = user

    def convert_iterable(self, inputs):
        return super().convert_iterable(inputs)

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        # Have we seen the source before?
        if data_object.source not in self.__sources_seen:
            self.__sources_seen.add(data_object.source)
            yield self._data_object_factory(
                'source',
                data_object.source
            )

        # Have we seen the species before?
        if data_object.taxon_id not in self.__species_seen:
            self.__species_seen.add(data_object.taxon_id)
            yield self._data_object_factory(
                'species',
                data_object.taxon_id
            )

        yield self._data_object_factory(
            'attribute',
            None,
            attributes={
                'value': data_object.attribute_value,
                'state': data_object.attribute_state
            },
            to_one={
                'source': self._data_object_factory(
                    'source',
                    data_object.source
                ),
                'species': self._data_object_factory(
                    'species',
                    data_object.taxon_id
                ),
                'attribute_key': self._data_object_factory(
                    'attribute_key',
                    data_object.attribute_key
                ),
                'user': self.__user
            }
        )
