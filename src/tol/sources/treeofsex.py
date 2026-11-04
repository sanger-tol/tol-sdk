# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .api import api
from .defaults import Defaults
from ..api_client import (
    ApiDataSource
)

def treeofsex(retries: int = 5, **kwargs) -> ApiDataSource:
    ds = api(
        url=os.getenv('TREEOFSEX_URL', Defaults.TREEOFSEX_URL),
        api_path=os.getenv('TREEOFSEX_API_PATH', Defaults.TREEOFSEX_API_PATH),
        api_data_path=os.getenv('TREEOFSEX_API_DATA_PATH', Defaults.TREEOFSEX_API_DATA_PATH),
        dataspace=None,
        token=os.getenv('TREEOFSEX_API_KEY'),
        retries=retries
    )
    return ds
