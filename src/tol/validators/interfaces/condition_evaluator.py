# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, Tuple, cast

from tol.core import DataObject


ConditionDict = Dict[str, str | Any | bool]
"""
The dict representation of a Condition. Conditions can be constructed
from such a dict through Condition.from_dict(condition_dict)
"""


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

    @staticmethod
    def from_dict(condition_dict: ConditionDict) -> 'Condition':
        """
        A means of instantiating a Condition from a dictionary.
        This is a separate method (rather than constructing with kwargs
        like `Condition(**condition_dict))`) to allow for both precense
        and type checking for each field.
        """
        try:
            # Extract fields
            field = condition_dict['field']
            operator = condition_dict['operator']
            value = condition_dict['value']
            is_error = condition_dict.get('is_error', True)

            # Ensure fields are the correct type
            if not isinstance(field, str) and not isinstance(operator, str):
                raise Exception(
                    f'Dictionary {condition_dict} not in valid format '
                    f'to convert to Condition (type of condition dict incorrect)'
                )

            return Condition(
                cast(str, field),
                cast(str, operator),
                value,
                cast(bool, is_error),
            )
        except IndexError as e:
            raise Exception(
                f'Dictionary {condition_dict} not in valid format '
                f'to convert to Condition (key "{e.args[0]}" not found)'
            )


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
