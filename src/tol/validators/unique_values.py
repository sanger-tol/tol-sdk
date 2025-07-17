# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject
from tol.core.validate import Validator


class UniqueValuesValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains unique values for specified keys.
    """

    def __init__(
        self,
        unique_keys: list[str],
        *,
        detail: str = 'Value is not unique',
        is_error: bool = True,
    ) -> None:

        super().__init__()

        self.__keys = unique_keys
        self.__detail = detail
        self.__is_error = is_error
        self.__duplicates: dict[str, list[str]] = {}
        self.__existing_values: dict[str, set] = {key: set() for key in unique_keys}

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        for key in obj.attributes:
            if key in self.__keys:
                if obj.attributes[key] in self.__existing_values[key]:
                    if key not in self.__duplicates:
                        self.__duplicates[key] = []
                    self.__duplicates[key].append(obj.attributes[key])
                else:
                    self.__existing_values[key].add(obj.attributes[key])

    def _post_validation(
        self,
        obj: DataObject,
    ) -> None:
        for key in self.__duplicates:
            self.__add_result(
                obj=obj,
                key=key,
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
