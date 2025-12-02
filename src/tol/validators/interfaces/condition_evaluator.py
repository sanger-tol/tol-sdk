# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Condition:
    left: Any
    operator: str
    right: Any


class ConditionEvaluator(ABC):
    """
    Interface to be inherited by validators. Evaluates the provided condition given its
    operator and operands
    """
    def _evaluate_condition(self, condition: Condition) -> bool:
        """
        Evaluates the provided condition given its operator and operands.
        If `operator` is not one of the supported operators, an exception is thrown.
        """
        match condition.operator:
            case '==':
                return condition.left == condition.right
            case '!=':
                return condition.left != condition.right
            case '<':
                return condition.left < condition.right
            case '<=':
                return condition.left <= condition.right
            case '>':
                return condition.left > condition.right
            case '>=':
                return condition.left >= condition.right
            case 'in':
                return condition.left in condition.right
            case _:
                raise Exception(f'VALIDATOR SETUP ERROR: `{condition.operator}` is not '
                                f'a supported operator for {type(self).__name__}')
