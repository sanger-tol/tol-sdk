# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, List

from tol.core import DataObject, Validator

from .interfaces import Condition, ConditionDict, ConditionEvaluator


class MutuallyExclusiveValidator(Validator, ConditionEvaluator):
    """
    Validates an incoming stream of `DataObject` instances,
    where the resultant field from field_one_condition must not
    have the same values for target_fields as the resultant
    field from field_two_condition
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        first_field_where: ConditionDict
        second_field_where: ConditionDict
        target_fields: List[str]
        detail: str | None = None

        def _get_error_message(self) -> str:
            # Extract conditions
            first_condition = Condition.from_dict(self.first_field_where)
            second_condition = Condition.from_dict(self.second_field_where)

            # Use a pre-defined, hard-coded detail message if one was not provided
            if self.detail is None:
                multiple_target_fields = len(self.target_fields) > 1
                possible_plural = 's' if multiple_target_fields else ''

                target_fields_str = ''
                if multiple_target_fields:
                    for index, field in enumerate(self.target_fields):
                        if index == 0:
                            # First field in the list
                            target_fields_str += f'{field}'
                        elif index == len(self.target_fields) - 1:
                            # Last field in the list
                            target_fields_str += f' and {field}'
                        else:
                            # Middle fields
                            target_fields_str += f', {field}'
                else:  # Only one field
                    target_fields_str = self.target_fields[0]

                return (
                    f'The field{possible_plural} {target_fields_str} cannot have the same '
                    f'value{possible_plural} both when {first_condition} and when '
                    f'{second_condition}'
                )
            else:
                return self.detail

    __slots__ = ['__config', '__first_list', '__second_list']
    __config: Config
    __first_list: List[Any]
    __second_list: List[Any]

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()

        self.__config = config
        self.__first_list = []
        self.__second_list = []

    def _validate_data_object(self, obj: DataObject) -> None:
        # Check first field
        if self._does_condition_pass(Condition.from_dict(self.__config.first_field_where), obj):
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
        elif self._does_condition_pass(Condition.from_dict(self.__config.second_field_where), obj):
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
