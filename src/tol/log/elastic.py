# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Callable

from .logger import Logger, LoggingDataSource, UserIdGetter
from ..api_base2.misc.auth_context import default_ctx_getter
from ..core import core_data_object
from ..elastic import ElasticDataSource


DOFactorySetter = Callable[[], Any]
"""The setter of `DataSource().data_object_factory`"""
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


def __create_elastic_datasource(
    uri: str,
    user: str,
    password: str,
    elastic_factory: ElasticFactory,
    do_factory_setter: DOFactorySetter
) -> ElasticDataSource:

    elastic_ds = elastic_factory(
        {
            'uri': uri,
            'user': user,
            'password': password,
            'index_prefix': '',
            'relationship_cfg': {}
        }
    )
    do_factory_setter(elastic_ds)
    return elastic_ds


def elastic_logger(
    uri: str,
    user: str,
    password: str,
    app_name: str,
    # the below (keyword) arguments are optional and used mainly for testing
    user_id_getter: UserIdGetter = lambda: default_ctx_getter().user_id,
    elastic_factory: ElasticFactory = lambda c: ElasticDataSource(c),
    logger_factory: LoggerFactory = lambda d, n, g: Logger(d, n, g),
    do_factory_setter: DOFactorySetter = lambda d: core_data_object(d)
) -> Logger:
    """
    Instantiates `Logger` using a bespoke instance of
    `ElasticDataSource`.
    """

    elastic_ds = __create_elastic_datasource(
        uri,
        user,
        password,
        elastic_factory,
        do_factory_setter
    )

    return logger_factory(
        elastic_ds,
        app_name,
        user_id_getter
    )
