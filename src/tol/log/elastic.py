# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Callable

from .logger import Logger, LoggingDataSource, UserIdGetter
from ..api_base2.misc.auth_context import default_ctx_getter
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
    app_name: str,
    user_id_getter: UserIdGetter = lambda: default_ctx_getter().user_id,
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

    return logger_factory(
        elastic_ds,
        app_name,
        user_id_getter
    )
