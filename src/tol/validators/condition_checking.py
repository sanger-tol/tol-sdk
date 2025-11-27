# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
# TODO: Could also be implemented as inheritence or as an interface

from typing import Any, Dict

from tol.core import Validator


Condition = Dict[str, str]


def check_condition(
    validator: Validator, field: str, left: Any, operator: str, right: Any
) -> bool:
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
            raise Exception(f'VALIDATOR SETUP ERROR: {operator}` is not a supported operator'
                            f'for {type(validator).__name__}')
