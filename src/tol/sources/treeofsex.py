# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..api_client import (
    ApiDataSource,
    create_api_datasource
)
from ..core import (
    core_data_object
)


def treeofsex(retries: int = 5, **kwargs) -> ApiDataSource:
    treeofsex = create_api_datasource(
        api_url=os.getenv('TREEOFSEX_URL', Defaults.TREEOFSEX_URL)
        + os.getenv('TREEOFSEX_API_PATH', Defaults.TREEOFSEX_API_PATH),
        token=os.getenv('TREEOFSEX_API_KEY'),
        data_prefix=os.getenv('TREEOFSEX_API_DATA_PATH', Defaults.TREEOFSEX_API_DATA_PATH),
        retries=retries
    )
    core_data_object(treeofsex)
    return treeofsex
