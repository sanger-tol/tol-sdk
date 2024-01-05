# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .api.elastic import api_elastic
from .api.sql import api_sql
from .base import DataSourceFixture
from .elastic_ds import elastic
from .sql_ds import sql


all_fixtures: tuple[DataSourceFixture] = (
    elastic,
    sql,
    api_elastic,
    api_sql
)
