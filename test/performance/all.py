# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable

# import all test-suite modules like this
from .relation import *


def __get_timed_methods() -> list[Callable]:
    """
    test-suite modules must have been imported
    using the `from .suite import *` syntax
    for this to work.
    """

    return [
        v
        for k, v in globals().items()
        if k.startswith('time_')
    ]


if __name__ == '__main__':
    for __timeit in __get_timed_methods():
        __timeit()
