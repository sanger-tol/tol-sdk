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


class BenchlingEntityToBenchlingWorklistItemConverterFactory():
    def __init__(self, worklist: DataObject):
        self._worklist = worklist

    def get_converter_class(self) -> DataObjectToDataObjectOrUpdateConverter:
        factory = self

        class BenchlingEntityToBenchlingWorklistItemConverter(
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

            def convert(self, data_object: DataObject | ErrorObject) \
                    -> Iterable[DataObject | ErrorObject]:
                if isinstance(data_object, ErrorObject):
                    yield data_object
                else:
                    ret = self._data_object_factory(
                        'worklist_item',
                        to_one={
                            'worklist': factory._worklist,
                            'item': data_object,
                        }
                    )
                    yield ret

        return BenchlingEntityToBenchlingWorklistItemConverter
