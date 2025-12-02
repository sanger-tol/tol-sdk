# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from dataclasses import dataclass
from typing import Any, Tuple

from tol.core import DataObject


@dataclass(slots=True)
class Condition:
    field: str
    operator: str
    value: Any
    # If this condition fails, should it be an error or a warning?
    # The reporting of this error or warning is done in the calling validator
    is_error: bool = True

    def __repr__(self) -> str:
        return f'{self.field} {self.operator} {self.value}'


class ConditionEvaluator(ABC):
    """
    Interface to be inherited by validators. Evaluates the provided condition given its
    operator and operands
    """
    def _evaluate_condition(self, condition: Condition, obj: DataObject) -> Tuple[bool, Any]:
        """
        Evaluates the provided condition given its operator and operands.
        If `operator` is not one of the supported operators, an exception is thrown.
        """
        value_to_test = obj.get_field_by_name(condition.field)

        match condition.operator:
            case '==':
                return (value_to_test == condition.value, value_to_test)
            case '!=':
                return (value_to_test != condition.value, value_to_test)
            case '<':
                return (value_to_test < condition.value, value_to_test)
            case '<=':
                return (value_to_test <= condition.value, value_to_test)
            case '>':
                return (value_to_test > condition.value, value_to_test)
            case '>=':
                return (value_to_test >= condition.value, value_to_test)
            case 'in':
                return (value_to_test in condition.value, value_to_test)
            case _:
                raise Exception(f'VALIDATOR SETUP ERROR: `{condition.operator}` is not '
                                f'a supported operator for {type(self).__name__}')
    
    def _does_condition_pass(self, condition: Condition, obj: DataObject) -> bool:
        """
        Helper function for when you only want to know whether the condition passes,
        and don't need the actual value
        """
        return self._evaluate_condition(condition, obj)[0]
