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

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        removing null fields from the DataObject
        """

        passes = True
        for field in self.__config.field_names:
            value = data_object.get_field_by_name(field)
            if value is None:
                passes = False
                break

        if passes:
            ret = self._data_object_factory(
                data_object.type,
                data_object.id,
                attributes=data_object.attributes
            )
            yield ret
