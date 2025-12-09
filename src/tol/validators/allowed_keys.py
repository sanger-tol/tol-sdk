# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import List

from tol.core import DataObject
from tol.core.validate import Validator


class AllowedKeysValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances,
    ensuring that they only have attributes of the given
    allowed keys.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        allowed_keys: List[str]
        is_error: bool = True
        detail: str = 'Key is not allowed'

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

        for key in obj.attributes:
            if key not in self.__config.allowed_keys:
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
