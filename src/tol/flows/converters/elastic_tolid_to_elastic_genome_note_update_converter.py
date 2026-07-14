# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticTolidToElasticGenomeNoteUpdateConverter(
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
        species = data_object.to_one_relationships['species']
        yield (
            None,
            {
                'species': self._data_object_factory(
                    'species',
                    species.id
                ),
                'tolid.id': data_object.id
            }
        )
