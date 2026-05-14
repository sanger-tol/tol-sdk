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


def benchling(api_key: str = None, folder_id: str = None, **kwargs) -> BenchlingDataSource:
    if api_key is None:
        api_key = os.getenv('BENCHLING_API_KEY')

    config = {
        'api_key': api_key,
        'url': os.getenv('BENCHLING_URL'),
        'registry_id': os.getenv('BENCHLING_REGISTRY_ID'),
        'project_id': os.getenv('BENCHLING_PROJECT_ID')
    }

    if folder_id:
        config['folder_id'] = folder_id

    benchling = BenchlingDataSource(config)
    core_data_object(benchling)

    return benchling
