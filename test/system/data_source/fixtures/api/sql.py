# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .util import ApiFixture
from ..sql_ds import sql


url = 'http://localhost:9021' if 'LOCALHOST' in os.environ else 'http://system-test-api-sql:5000'
api_sql = ApiFixture(sql, url)
