# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping
from typing import Iterator

from flask import Flask

from tol.api_base2.blueprint import (
    _config_blueprint,
    _core_blueprint
)
from tol.core.factory import core_data_object
from tol.core.operator.operator_config import DefaultOperatorConfig
from tol.elastic import ElasticDataSource

from .util import elastic_datasource
from ...data_source.types import TEST_OBJECT_TYPES


TEST_ATTRIBUTE_TYPES = {
    'root': {
        'str_column': 'str',
        'int_column': 'int',
        'datetime_column': 'datetime',
        'bool_column': 'bool'
    },
    'related': {
        'str_column': 'str',
        'int_column': 'int',
        'datetime_column': 'datetime',
        'bool_column': 'bool'
    }
}


class _ModifiedElasticDataSource(ElasticDataSource):
    """"""

    @property
    def supported_types(self) -> list[str]:
        return TEST_OBJECT_TYPES

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return TEST_ATTRIBUTE_TYPES


def _modified_elastic_ds() -> _ModifiedElasticDataSource:
    elastic_ds = elastic_datasource(
        class_=_ModifiedElasticDataSource
    )
    core_data_object(elastic_ds)
    return elastic_ds


class _DataSourceDict(Mapping):

    def __getitem__(self, __k: str) -> ElasticDataSource:

        return _modified_elastic_ds()

    def __iter__(self) -> Iterator[str]:
        return iter(TEST_OBJECT_TYPES)

    def __len__(self) -> int:
        return len(TEST_OBJECT_TYPES)


data_bp = _core_blueprint(
    _DataSourceDict(),
    '/data'
)


elastic_ds = _modified_elastic_ds()


config_bp = _config_blueprint(
    '/_config',
    (elastic_ds,),
    DefaultOperatorConfig(elastic_ds)
)
data_bp.register_blueprint(config_bp)


app = Flask(__name__)
app.register_blueprint(data_bp)
