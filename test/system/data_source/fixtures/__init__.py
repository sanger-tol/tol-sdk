# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .api.elastic import api_elastic
from .api.sql import api_sql
from .base import DataSourceFixture
from .elastic_ds import elastic


all_fixtures: tuple[DataSourceFixture] = (
    elastic,
    api_elastic,
    api_sql
)
