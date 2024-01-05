# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from tol.elastic import ElasticDataSource


def get_prefix() -> str:
    elastic_prefix = os.environ['ELASTIC_INDEX_PREFIX']
    uuid_prefix = os.environ['UUID_PREFIX']
    return f'{elastic_prefix}-test-{uuid_prefix}'


def elastic_datasource(
    class_: ElasticDataSource = ElasticDataSource
) -> ElasticDataSource:

    return class_(
        {
            'uri': os.environ['ELASTIC_URI'],
            'user': os.environ['ELASTIC_USER'],
            'password': os.environ['ELASTIC_PASSWORD'],
            'index_prefix': get_prefix(),
            'relationship_cfg': {}
        }
    )
