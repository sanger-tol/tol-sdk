# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..benchling import (
    BenchlingDataSource
)
from ..core import (
    core_data_object
)


def benchling(**kwargs) -> BenchlingDataSource:
    benchling = BenchlingDataSource(
        {
            'api_key': os.getenv('BENCHLING_API_KEY'),
            'url': os.getenv('BENCHLING_URL'),
            'registry_id': os.getenv('BENCHLING_REGISTRY_ID'),
            'project_id': os.getenv('BENCHLING_PROJECT_ID')
        }
    )
    core_data_object(benchling)

    return benchling
