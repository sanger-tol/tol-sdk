# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, List

from tol.core import DataObject, Validator

from .interfaces import Condition, ConditionEvaluator


# TODO: Move to be local class of validator
@dataclass(slots=True, frozen=True, kw_only=True)
class MutuallyExclusiveConfig:
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


class MutuallyExclusiveValidator(Validator, ConditionEvaluator):
    __slots__ = [
        '__config', '__target_fields_seen_for_first_field', '__target_fields_seen_for_second_field'
    ]
    __config: MutuallyExclusiveConfig
    __target_field_values_seen_for_first_field: List[Any]
    __target_field_values_seen_for_second_field: List[Any]

    def __init__(self, config: MutuallyExclusiveConfig) -> None:
        super().__init__()
        
        self.__config = config
        self.__target_field_values_seen_for_first_field = []
        self.__target_field_values_seen_for_second_field = []

    def _validate_data_object(self, obj: DataObject) -> None:
        # if self._evaluate_condition(self.__config.first_field_where, obj):
        #     self.__target_field_values_seen_for_first_field.append(
        #         [
        #             obj.get_field_by_name(target_field)
        #             for target_field in self.__config.target_fields
        #         ]
        #     )
        # elif self._evaluate_condition(self.__config.second_field_where, obj):
        #     self.add_error(
        #         object_id=obj.id,
        #         detail=self.__config._get_error_message()
        #     )
