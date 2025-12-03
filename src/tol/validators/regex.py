# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from typing import Any, List

from tol.core import DataObject
from tol.core.validate import Validator


@dataclass(frozen=True, kw_only=True)
class Regex:
    key: str
    regex: str

    is_error: bool = True
    detail: str = 'Value is not allowed for given key'

    def is_allowed(self, __v: Any) -> bool:
        # Check regex
        return re.search(self.regex, str(__v or ''))


class RegexValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances
    according to the specified allowed values for a given
    key.
    """
    __slots__ = ['__config']
    __config: List[Regex]

    def __init__(
        self,
        config: List[Regex]
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
    ) -> list[Regex]:
        return [
            a for a in self.__config
            if a.key == key
        ]

    def __add_result(
        self,
        obj: DataObject,
        c: Regex,
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
