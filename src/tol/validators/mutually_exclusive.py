# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import List

from tol.core import DataObject, Validator

from .interfaces import ConditionEvaluator, Condition


@dataclass(slots=True, frozen=True)
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
    __slots__ = ['__config']
    __config: MutuallyExclusiveConfig
    
    def __init__(self, config: MutuallyExclusiveConfig) -> None:
        super().__init__()
    
    def _validate_data_object(self, obj: DataObject) -> None:
        pass
