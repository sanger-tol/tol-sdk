# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class PrefixFieldConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field_name: str
        prefix: str

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        Ensures the configured field value
        starts with the configured prefix. If the field is None, it is
        left as-is.
        """

        value = data_object.get_field_by_name(
            self.__config.field_name
        )

        if value is not None:
            value_str = str(value)
            if not value_str.startswith(self.__config.prefix):
                value = f'{self.__config.prefix}{value_str}'

        ret = self._data_object_factory(
            data_object.type,
            data_object.id,
            attributes={
                **data_object.attributes,
                self.__config.field_name: value
            }
        )
        yield ret
