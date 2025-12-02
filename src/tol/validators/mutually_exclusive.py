# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, List

from tol.core import DataObject, Validator

from .interfaces import Condition, ConditionEvaluator


class MutuallyExclusiveValidator(Validator, ConditionEvaluator):
    """
    Validates an incoming stream of `DataObject` instances,
    where the resultant field from field_one_condition must not
    have the same values for target_fields as the resultant
    field from field_two_condition
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        first_field_where: Condition
        second_field_where: Condition
        target_fields: List[str]
        error_message: str | None = None

        def _get_error_message(self) -> str:
            if self.error_message is None:
                return (
                    f'The conditions {self.first_field_where} and {self.second_field_where} '
                    f'must be mutually exclusive'
                )
            else:
                return self.error_message

    __slots__ = ['__config', '__first_list', '__second_list']
    __config: Config
    __first_list: List[Any]
    __second_list: List[Any]

    def __init__(self, config: Config) -> None:
        super().__init__()

        self.__config = config
        self.__first_list = []
        self.__second_list = []

    def _validate_data_object(self, obj: DataObject) -> None:
        # Check first field
        if self._evaluate_condition(self.__config.first_field_where, obj):
            # Check whether the values of the target fields were found in the second list
            if [
                obj.get_field_by_name(target_field)
                for target_field in self.__config.target_fields
            ] in self.__second_list:
                self.add_error(
                    object_id=obj.id,
                    detail=self.__config._get_error_message()
                )

            # Add the values of the target fields to the first list
            self.__first_list.append(
                [
                    obj.get_field_by_name(target_field)
                    for target_field in self.__config.target_fields
                ]
            )
        # Check second field (same as the first condition, but for the second!)
        elif self._evaluate_condition(self.__config.second_field_where, obj):
            # Check whether the values of the target fields were found in the first list
            if [
                obj.get_field_by_name(target_field)
                for target_field in self.__config.target_fields
            ] in self.__first_list:
                self.add_error(
                    object_id=obj.id,
                    detail=self.__config._get_error_message()
                )

            # Add the values of the target fields to the second list
            self.__second_list.append(
                [
                    obj.get_field_by_name(target_field)
                    for target_field in self.__config.target_fields
                ]
            )
        # If neither condition passes, the data object must be valid (for this validator anyway!)
