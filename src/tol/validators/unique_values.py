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
        unique_keys: list[list[str] | str],
        *,
        detail: str = 'Value is not unique',
        is_error: bool = True,
    ) -> None:
        

        super().__init__()

        self.__keys = unique_keys
        self.__detail = detail
        self.__is_error = is_error
        self.__duplicates: dict[str, list[str]] = {}
        self.__existing_values: dict[str, set] = {}
        for key in self.__keys:
            if isinstance(key, str):
                self.__existing_values[key] = set()
            elif isinstance(key, list):
                concat_key = '/'.join(key)
                self.__existing_values[concat_key] = set()

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        for unique_key in self.__keys:
            if isinstance(unique_key, list):
                concat = ''
                for key in unique_key:
                    concat = concat + '/' + (str(obj.attributes[key]))
                if concat in self.__existing_values['/'.join(unique_key)]:
                    self._duplicate_checks(
                        key=key,
                        value=concat
                    )
            else:
                if obj.attributes[unique_key] in self.__existing_values[unique_key]:
                    self._duplicate_checks(
                        key=unique_key,
                        value=obj.attributes[unique_key]
                    )
                else:
                    self.__existing_values[unique_key].add(obj.attributes[unique_key])
                    

    def _duplicate_checks(
        self,
        key: str,
        value: str
    ):
        if key not in self.__duplicates:
            self.__duplicates[key] = []
        self.__duplicates[key].append(value)

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
