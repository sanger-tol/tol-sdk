# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject
from tol.core.validate import Validator


class AllowedKeysValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances,
    ensuring that they only have attributes of the given
    allowed keys.
    """

    def __init__(
        self,
        allowed_keys: list[str],
        *,
        is_error: bool = True,
        detail: str = 'Key is not allowed'
    ) -> None:

        super().__init__()

        self.__keys = allowed_keys
        self.__is_error = is_error
        self.__detail = detail

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        for key in obj.attributes:
            if key not in self.__keys:
                self.__add_result(
                    obj,
                    key,
                )

    def __add_result(
        self,
        obj: DataObject,
        key: str,
    ) -> None:

        if self.__is_error:
            self.add_error(
                object_id=obj.id,
                detail=self.__detail,
                field=key,
            )
        else:
            self.add_warning(
                object_id=obj.id,
                detail=self.__detail,
                field=key,
            )
