# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..benchling import (
    BenchlingWarehouseDataSource
)
from ..core import (
    core_data_object
)


def benchling_warehouse(**kwargs) -> BenchlingWarehouseDataSource:
    benchling_warehouse = BenchlingWarehouseDataSource({
        'username': os.getenv('BENCHLING_USER'),
        'password': os.getenv('BENCHLING_PASSWORD'),
        'database': os.getenv('BENCHLING_DB'),
        'hostname': os.getenv('BENCHLING_HOST'),
        'port': os.getenv('BENCHLING_PORT'),
        'schema': os.getenv('BENCHLING_SCHEMA')})
    core_data_object(benchling_warehouse)
    return benchling_warehouse
