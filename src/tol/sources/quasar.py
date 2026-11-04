# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .api import api
from .defaults import Defaults
from ..api_client import (
    ApiDataSource
)

def quasar(retries: int = 5, **kwargs) -> ApiDataSource:
    ds = api(
        url=os.getenv('QUASAR_URL', Defaults.QUASAR_URL),
        api_path=os.getenv('QUASAR_API_PATH', Defaults.QUASAR_API_PATH),
        api_data_path=os.getenv('QUASAR_API_DATA_PATH', Defaults.QUASAR_API_DATA_PATH),
        dataspace=os.getenv('QUASAR_DATASPACE', Defaults.QUASAR_DATASPACE),
        token=os.getenv('QUASAR_API_KEY'),
        retries=retries
    )
    return ds
