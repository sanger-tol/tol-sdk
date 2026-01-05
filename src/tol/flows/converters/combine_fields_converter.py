# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class CombineFieldsConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field1: str
        field2: str
        dest_field: str
        lowercase_field1: bool

    __slots__ = ('__config',)
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        Concatenates the values of two fields and stores the result in a new field.
        The first field's value may be lowercased if specified in the configuration.
        The destination field name is given by the configuration.
        """

        val1 = data_object.get_field_by_name(self.__config.field1)
        val2 = data_object.get_field_by_name(self.__config.field2)
        attributes = dict(data_object.attributes)

        if val1 is not None and val2 is not None:
            part1 = str(val1).lower() if self.__config.lowercase_field1 else str(val1)
            attributes[self.__config.dest_field] = f'{part1}{val2}'

        yield self._data_object_factory(
            data_object.type,
            data_object.id,
            attributes=attributes,
        )
