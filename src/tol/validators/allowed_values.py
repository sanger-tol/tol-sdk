# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, List

from tol.core import DataObject
from tol.core.validate import Validator


@dataclass(frozen=True, kw_only=True)
class AllowedValues:
    key: str
    values: List[Any]

    is_error: bool = True
    detail: str = 'Value is not allowed for given key'

    def is_allowed(self, __v: Any) -> bool:
        return __v in self.values


class AllowedValuesValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances
    according to the specified allowed values for a given
    key.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        allowed_values: List[AllowedValues]

    __slots__ = ['__config']
    __config: Config

    def __init__(
        self,
        config: Config
    ) -> None:

        super().__init__()

        self.__config = config

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        for k, v in obj.attributes.items():
            self.__validate_attribute(obj, k, v)

    def __validate_attribute(
        self,
        obj: DataObject,
        key: str,
        value: Any,
    ) -> None:

        config = self.__filter_config(key)

        for c in config:
            if not c.is_allowed(value):
                self.__add_result(obj, c)

    def __filter_config(
        self,
        key: str,
    ) -> list[AllowedValues]:

        return [
            a for a in self.__config.allowed_values
            if a.key == key
        ]

    def __add_result(
        self,
        obj: DataObject,
        c: AllowedValues,
    ) -> None:

        if c.is_error:
            self.add_error(
                object_id=obj.id,
                detail=c.detail,
                field=c.key
            )
        else:
            self.add_warning(
                object_id=obj.id,
                detail=c.detail,
                field=c.key,
            )
