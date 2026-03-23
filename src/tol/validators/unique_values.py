# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Dict, List, Set

from tol.core import DataObject
from tol.core.validate import Validator


class UniqueValuesValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains unique values for specified keys.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        unique_keys: List[List[str] | str]
        detail: str = 'Value is not unique'
        is_error: bool = True

    __slots__ = ['__config', '__duplicates', '__existing_values']
    __config: Config
    __duplicates: Dict[str, List[str]]
    __existing_values: Dict[str, Set]

    def __init__(
        self,
        config: Config,
        **kwargs
    ) -> None:

        super().__init__()

        self.__config = config
        self.__duplicates = {}
        self.__existing_values = {}
        for key in self.__config.unique_keys:
            if isinstance(key, str):
                self.__existing_values[key] = set()
            elif isinstance(key, list):
                concat_key = '/'.join(key)
                self.__existing_values[concat_key] = set()

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        for unique_key in self.__config.unique_keys:
            if isinstance(unique_key, list):
                concat = ''
                for key in unique_key:
                    concat = concat + '/' + (str(obj.attributes[key]))
                if concat in self.__existing_values['/'.join(unique_key)]:
                    self.__duplicate_checks(
                        key=key,
                        value=concat
                    )
                else:
                    self.__existing_values['/'.join(unique_key)].add(concat)

            else:
                if obj.attributes[unique_key] in self.__existing_values[unique_key]:
                    self.__duplicate_checks(
                        key=unique_key,
                        value=obj.attributes[unique_key]
                    )
                else:
                    self.__existing_values[unique_key].add(obj.attributes[unique_key])

    def __duplicate_checks(
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
