# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import sys
from functools import reduce
from typing import Any, Callable

import click

from performance.utils import LimitExceededError

# import all test-suite modules like this
from .relation import *  # noqa


def __get_timed_methods() -> list[Callable]:
    """
    test-suite modules must have been imported
    using the `from .suite import *` syntax
    for this to work.
    """

    def __is_timed(v: Any) -> bool:
        return getattr(
            v,
            '__benchmark__',
            False
        ) is True

    return [
        v
        for v in globals().values()
        if __is_timed(v)
    ]


def __run_methods(
    timed_methods: list[Callable]
) -> None:

    def __run(
        list_exc: list[LimitExceededError],
        m: Callable,
    ) -> list[LimitExceededError]:

        try:
            m()
        except LimitExceededError as e:
            list_exc.append(e)

        return list_exc

    errors = reduce(
        __run,
        timed_methods,
        []
    )

    if errors:
        click.secho(
            f'\n{len(errors)} error(s).',
            fg='red'
        )
        sys.exit(1)
    else:
        click.secho(
            '\nAll benchmarks within tolerance. :)',
            fg='green'
        )


def main() -> None:
    methods = __get_timed_methods()

    __run_methods(methods)


if __name__ == '__main__':
    main()
