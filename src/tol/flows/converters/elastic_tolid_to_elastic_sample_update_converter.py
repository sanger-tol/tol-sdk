# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticTolidToElasticSampleUpdateConverter(
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

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object.species is not None and data_object.specimen is not None:
            species = data_object.to_one_relationships['species']
            specimen = data_object.to_one_relationships['specimen']
            yield (
                None,
                {
                    'tolid': self._data_object_factory(
                        'tolid',
                        data_object.id
                    ),
                    'species.id':
                        data_object.requested_taxonomy_id
                        if data_object.requested_taxonomy_id is not None
                        else species.id,
                    'specimen.id': specimen.id
                }
            )
