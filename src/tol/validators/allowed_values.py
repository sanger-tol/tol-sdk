# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, List

from tol.core import DataObject
from tol.core.validate import Validator


class AllowedValuesValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances
    according to the specified allowed values for a given
    key.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field: str
        allowed_values: List[Any]
        is_error: bool = True
        detail: str = 'Value is not allowed for the given key'

    __slots__ = ['__config']
    __config: Config

    def __init__(
        self,
        config: Config,
        **kwargs
    ) -> None:

        super().__init__()

        self.__config = config

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        for key, value in obj.attributes.items():
            if key == self.__config.field and value not in self.__config.allowed_values:
                self.__add_result(obj, key)

    def __add_result(
        self,
        obj: DataObject,
        key: str,
    ) -> None:

        if self.__config.is_error:
            self.add_error(
                object_id=obj.id,
                detail=self.__config.detail,
                field=key
            )
        else:
            self.add_warning(
                object_id=obj.id,
                detail=self.__config.detail,
                field=key,
            )
