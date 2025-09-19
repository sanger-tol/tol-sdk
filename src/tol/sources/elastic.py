# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..elastic import (
    ElasticDataSource
)


def elastic(
        environment: str = None,
        product: str = None,
        **kwargs
) -> ElasticDataSource:

    # Set up the correct environment. Can be passed in as a parameter
    # or be ELASTIC_ENVIRONMENT environment variable
    # or not be set
    if environment is None:
        environment = os.getenv('ELASTIC_ENVIRONMENT', 'production')
    if product is None:
        product = os.getenv('ELASTIC_PRODUCT', 'portal')
    index_suffix = f'-{product}' if product else ''
    index_suffix += f'-{environment}' if environment else ''
    elastic = ElasticDataSource({
        'uri': os.getenv('ELASTIC_URI'),
        'user': os.getenv('ELASTIC_USER'),
        'password': os.getenv('ELASTIC_PASSWORD'),
        'index_prefix': os.getenv('ELASTIC_INDEX_PREFIX') + index_suffix},
        **kwargs
    )
    core_data_object(elastic)
    return elastic
