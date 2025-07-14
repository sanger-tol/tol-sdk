# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .util import ApiFixture
from ..elastic_ds import elastic


url = 'http://localhost:9200' if 'LOCALHOST' in os.environ else 'http://system-test-api-elastic:5000'
api_elastic = ApiFixture(elastic, url)
