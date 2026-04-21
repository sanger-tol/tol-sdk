# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolidSpecimenToElasticTolidConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

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
