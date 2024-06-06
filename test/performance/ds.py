# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from system.data_source.services.sql import (
    create_tables
)

from tol.api_client2 import create_api_datasource
from tol.core import core_data_object


create_tables()

api_ds = create_api_datasource(
    'http://system-test-api-sql:5000'
)
core_data_object(api_ds)
