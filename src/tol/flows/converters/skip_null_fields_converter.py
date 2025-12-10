# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class SkipNullFieldsConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field_names: list[str]

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory
        self._exists_cache = []

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        removing null fields from the DataObject
        """
        
        for field in self.__config.field_names:
            if field in data_object.attributes.keys():
                if self.check_exists(data_object, field):
                    self._exists_cache.append(field)
        
        if self._exists_cache == self.__config.field_names:
            ret = self._data_object_factory(
                data_object.type,
                data_object.id,
                attributes=data_object.attributes
            )
            yield ret
        
        else:
            yield None


    def check_exists(self, data_object: DataObject, field: str) -> bool:
        if data_object.attributes[field] and data_object.attributes[field] is not None:
            return True
        return False