# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    ErrorObject
)


class BenchlingEntityToBenchlingWorklistItemConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        worklist: object  # DataObject — kept as `object` to avoid circular imports

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject | ErrorObject) \
            -> Iterable[DataObject | ErrorObject]:
        if isinstance(data_object, ErrorObject):
            yield data_object
        else:
            ret = self._data_object_factory(
                'worklist_item',
                to_one={
                    'worklist': self.__config.worklist,
                    'item': data_object,
                }
            )
            yield ret
