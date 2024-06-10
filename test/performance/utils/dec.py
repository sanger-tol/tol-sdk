# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import functools as f
import time
import typing as t

import click


BENCHMARK_HOOK = t.Callable[[], None]


__BENCHMARK_DEC = t.Union[
    BENCHMARK_HOOK,
    t.Callable[
        [BENCHMARK_HOOK],
        BENCHMARK_HOOK
    ]
]


class LimitExceededError(Exception):

    def __init__(
        self,
        hook_name: str,
        fail: float
    ) -> None:

        self.__message = (
            f'{hook_name} exceeded its "fail" '
            f'duration ({fail:.3f}).'
        )

        click.secho(
            self.__message,
            fg='red'
        )

        super().__init__(self.__message)


def __report_result(
    average: float,
    hook_name: str,
    warn: float | None,
    fail: float | None
) -> None:

    click.secho(
        f'{hook_name} - {average:.3f} milliseconds'
    )

    if fail is not None and average > fail:
        raise LimitExceededError(hook_name, fail)

    if warn is not None and average > warn:
        message = (
            f'{hook_name} exceeded its "warn" '
            f'duration ({warn:.3f}).'
        )
        click.secho(message, fg='yellow')


def benchmark(
    arg_hook: BENCHMARK_HOOK | None = None,
    *,
    repetitions: int = 10,
    warn: float | None = None,
    fail: float | None = None
) -> __BENCHMARK_DEC:
    """
    Benchmarks the time taken by a hook.

    Defaults to 10 repetitions.

    These benchmark cases must be isolated -
    use UUID's for any unique data.

    `assert` that the data is correct.

    Specify `warn`, in milliseconds, to warn if
    the average goes above.

    Specify `fail`, also in milliseconds, to
    fail test test above this.
    """

    def decorator(
        hook: BENCHMARK_HOOK
    ) -> BENCHMARK_HOOK:

        hook_name = hook.__name__

        @f.wraps(hook)
        def wrapper() -> None:
            start = time.perf_counter()

            for _ in range(repetitions):
                hook()

            stop = time.perf_counter()

            average = ((stop - start) / repetitions) * 1000

            __report_result(
                average,
                hook_name,
                warn,
                fail,
            )

        wrapper.__benchmark__ = True

        return wrapper

    if callable(arg_hook):
        return decorator(arg_hook)
    else:
        return decorator
