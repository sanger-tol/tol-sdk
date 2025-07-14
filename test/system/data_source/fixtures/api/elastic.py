# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .util import ApiFixture
from ..elastic_ds import ElasticFixture
from ...services.util import get_prefix


url = (
    'http://localhost:9023' if 'LOCALHOST' in os.environ else 'http://system-test-api-elastic:5000'
)
elastic = ElasticFixture(
    f'{get_prefix()}-api'
)
api_elastic = ApiFixture(elastic, url)
