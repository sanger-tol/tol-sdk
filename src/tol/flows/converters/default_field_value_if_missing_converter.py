# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class DefaultFieldValueIfMissingConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field_name: str
        default_value: str

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        Adds a default value for a configured field if missing, empty, or None
        """

        attributes = dict(data_object.attributes)

        current_value = attributes.get(self.__config.field_name)
        if not current_value:
            attributes[self.__config.field_name] = self.__config.default_value

        ret = self._data_object_factory(
            data_object.type,
            data_object.id,
            attributes=attributes
        )
        yield ret
