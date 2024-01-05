# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .util import ApiFixture
from ..sql_ds import sql


api_sql = ApiFixture(sql, 'system-test-api-sql')
