# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TreeofsexUploadToTreeofsexwhSpeciesConverter(
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
            'species',
            data_object.species,
            attributes={
                data_object.key: data_object.value,
                data_object.key + '_reference': data_object.reference
                # We will want to change this to be like the below
                # data_object.key: [
                #     {
                #         'value': data_object.value,
                #         'source': data_object.reference,
                #     }
                # ]
            }
        )
        yield ret
