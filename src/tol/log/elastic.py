# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Callable

from .logger import Logger
from ..elastic import ElasticDataSource


ElasticFactory = Callable[
    [dict[str, Any]],
    ElasticDataSource
]


def elastic_logger(
    uri: str,
    user: str,
    password: str,
    factory: ElasticFactory = lambda c: ElasticDataSource(c)
) -> Logger:
    """
    Instantiates `Logger` using a bespoke instance of
    `ElasticDataSource`.
    """

    elastic_ds = ElasticDataSource(
        {
            'uri': uri,
            'user': user,
            'password': password
        }
    )
