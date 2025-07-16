# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Flask

from tol.api_base import data_blueprint
from tol.core.factory import core_data_object
from tol.elastic import ElasticDataSource

from ..util import (
    elastic_datasource,
    get_prefix,
    wait_for_ready
)


def application() -> Flask:
    wait_for_ready()
    prefix = get_prefix(extra_prefix='')

    class _ProxyElasticDS(ElasticDataSource):
        def __init__(self, target: ElasticDataSource) -> None:
            self._target = target

        @property
        def target(self) -> ElasticDataSource:
            return self._target

        @target.setter
        def target(self, new_val: ElasticDataSource) -> None:
            self._target = new_val

        def __getattr__(self, name: str):
            if name == 'target':
                return object.__getattribute__(self, 'target')

            return getattr(self._target, name)

    # create an initial target, just enough
    initial_target: ElasticDataSource = create_autospec(
        ElasticDataSource,
        spec_set=True,
    )
    initial_target.supported_types = ['root', 'related']

    # instantiate the proxy
    proxy_ds = _ProxyElasticDS(initial_target)
    data_bp = data_blueprint(proxy_ds)

    app = Flask(__name__)
    app.register_blueprint(data_bp)

    @app.post('/resetz')
    def resetz():
        """
        `ElasticDataSource` caches alias->index lookup

        Need to clear cache and re-instantiate before every test
        """

        # reset the `_get_indices` cache
        ElasticDataSource._get_indices.cache_clear()

        new_ds = elastic_datasource(prefix)
        core_data_object(new_ds)

        proxy_ds.target = new_ds

        return {}, 200

    return app
