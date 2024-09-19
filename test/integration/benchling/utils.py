# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable

import pytest


TEST_TYPES = [
    'tissue',  # `CustomEntity`
    'plate',
    'transfer',
]


def against_types(
    object_types: list[str]
) -> Callable[[], Callable[[], None]]:
    """
    Repeats the decorated test for each value
    in `object_types`.
    """

    params = [
        pytest.param(t, id=t)
        for t in object_types
    ]

    return pytest.mark.parametrize(
        'object_type',
        params
    )


against_all = against_types(
    TEST_TYPES
)
