# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import functools as f
import logging as l
import time
import typing as t


BENCHMARK_HOOK = t.Callable[[], None]


__BENCHMARK_DEC = t.Union[
    BENCHMARK_HOOK,
    t.Callable[
        [BENCHMARK_HOOK],
        BENCHMARK_HOOK
    ]
]


def benchmark(
    arg_hook: BENCHMARK_HOOK | None = None,
    *,
    repetitions: int = 10
) -> __BENCHMARK_DEC:
    """
    Benchmarks the time taken by a hook.

    Defaults to 10 repetitions.

    These benchmark cases must be isolated -
    use UUID's for any unique data.

    `assert` that the data is correct.
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

            average = (stop - start) / repetitions * 1000

            print(
                f'{hook_name} - {average:.3f} milliseconds'
            )

        return wrapper

    if callable(arg_hook):
        return decorator(arg_hook)
    else:
        return decorator
