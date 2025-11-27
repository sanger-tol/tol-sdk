# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Any


class ConditionEvaluator(ABC):
    """
    Interface to be inherited by validators. Evaluates the provided condition given its
    operator and operands
    """
    def _evaluate_condition(self, left: Any, operator: str, right: Any) -> bool:
        """
        Evaluates the provided condition given its operator and operands.
        If `operator` is not one of the supported operators, an exception is thrown.
        """
        match operator:
            case '==':
                return left == right
            case '!=':
                return left != right
            case '<':
                return left < right
            case '<=':
                return left <= right
            case '>':
                return left > right
            case '>=':
                return left >= right
            case 'in':
                return left in right
            case _:
                raise Exception(f'VALIDATOR SETUP ERROR: `{operator}` is not a supported operator'
                                f'for {type(self).__name__}')
