# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import time

import requests

from .util import ApiFixture
from ..elastic_ds import ElasticFixture
from ...services.util import get_prefix


class ElasticApiFixture(ApiFixture):
    def before_test(self) -> None:
        super().before_test()

        # force an `elastic_ds` reset
        requests.post(
            f'{self.url}/resetz'
        )


# need to add `'api'` as an `extra_prefix`, as we're not
# in the API container, so it's not already there on
# the `ELASTIC_INDEX_PREFIX` env variable
prefix = get_prefix(extra_prefix='api')
url = (
    'http://localhost:9023' if 'LOCALHOST' in os.environ else 'http://system-test-api-elastic:5000'
)
elastic = ElasticFixture(prefix)
api_elastic = ElasticApiFixture(elastic, url)
