from abc import ABC
from typing import Any

class ConditionEvaluator(ABC):
    def _evaluate_condition(self, left: Any, operator: str, right: Any) -> bool:
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
