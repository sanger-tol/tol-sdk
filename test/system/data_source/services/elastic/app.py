# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import Flask

from tol.api_base import data_blueprint
from tol.core import core_data_object
from tol.elastic import ElasticDataSource

from ..util import (
    create_indices,
    elastic_datasource,
    get_prefix,
    wait_for_ready
)


def application() -> Flask:
    wait_for_ready()
    prefix = get_prefix(extra_prefix='')

    create_indices(prefix)

    elastic_ds = elastic_datasource(prefix)
    core_data_object(elastic_ds)

    data_bp = data_blueprint(elastic_ds)

    app = Flask(__name__)
    app.register_blueprint(data_bp)

    @app.post('/resetz')
    def resetz():
        """
        `ElasticDataSource` caches alias->index lookup

        Need to clear this cache before every test
        """

        # reset the caches
        ElasticDataSource._get_indices.cache_clear()
        ElasticDataSource.attribute_types.cache_clear()

        return {}, 200

    return app
