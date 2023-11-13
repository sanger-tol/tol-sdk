# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Callable

from .logger import Logger, LoggingDataSource, UserIdGetter
from ..core import core_data_object
from ..elastic import ElasticDataSource


ElasticFactory = Callable[
    [dict[str, Any]],
    ElasticDataSource
]
LoggerFactory = Callable[
    [
        LoggingDataSource,
        str,
        UserIdGetter
    ],
    Logger
]


def elastic_logger(
    uri: str,
    user: str,
    password: str,
    elastic_factory: ElasticFactory = lambda c: ElasticDataSource(c),
    logger_factory: LoggerFactory = lambda d, n, g: Logger(d, n, g)
) -> Logger:
    """
    Instantiates `Logger` using a bespoke instance of
    `ElasticDataSource`.
    """

    elastic_ds = elastic_factory(
        {
            'uri': uri,
            'user': user,
            'password': password,
            'index_prefix': '',
            'relationship_cfg': {}
        }
    )
    core_data_object(elastic_ds)
