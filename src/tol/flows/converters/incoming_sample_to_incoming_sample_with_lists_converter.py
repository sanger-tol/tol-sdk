# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class IncomingSampleToIncomingSampleWithListsConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        fields_to_convert: str
        separator: str = '|'

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        converting the samples DataObject into ENA format
        """

        ret = self._data_object_factory(
            data_object.type,
            data_object.id,
            attributes={
                k: v for k, v in data_object.attributes.items()
                if k not in self.__config.fields_to_convert
            } | {
                field: self.__convert_to_list(data_object.get_field_by_name(field))
                for field in self.__config.fields_to_convert
            }
        )
        yield ret

    def __convert_to_list(self, value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(self.__config.separator)]
