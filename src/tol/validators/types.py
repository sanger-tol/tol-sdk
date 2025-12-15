# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime, time

from tol.core import DataObject
from tol.core.validate import Validator


class TypesValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances,
    ensuring that they only have attributes of the given
    allowed keys.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        allowed_types: dict[str, str]
        is_error: bool = True
        detail: str = 'Value is of incorrect type'

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

        type_map = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'datetime': datetime,
            'time': time
        }
        for key, expected_type in self.__config.allowed_types.items():
            if key in obj.attributes:
                actual_value = obj.get_field_by_name(key)
                if actual_value is None:
                    continue
                type_class = type_map.get(expected_type)
                if type_class and not isinstance(actual_value, type_class):
                    self.__add_result(
                        obj,
                        key,
                    )
                if type_class and isinstance(actual_value, type_class):
                    # Special case for bool since isinstance(True, int) is True
                    if expected_type == 'int' and isinstance(actual_value, bool):
                        self.__add_result(
                            obj,
                            key,
                        )

    def __add_result(
        self,
        obj: DataObject,
        key: str,
    ) -> None:

        if self.__config.is_error:
            self.add_error(
                object_id=obj.id,
                detail=self.__config.detail,
                field=key,
            )
        else:
            self.add_warning(
                object_id=obj.id,
                detail=self.__config.detail,
                field=key,
            )
