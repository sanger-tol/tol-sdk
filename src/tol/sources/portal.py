# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .api import api
from .defaults import Defaults
from ..api_client import (
    ApiDataSource
)

def portal(
        retries: int = 5,
        dataspace: str = 'tol_production',
        **kwargs
) -> ApiDataSource:
    ds = api(
        url=os.getenv('PORTAL_URL', Defaults.PORTAL_URL),
        api_path=os.getenv('PORTAL_API_PATH', Defaults.PORTAL_API_PATH),
        api_data_path=os.getenv('PORTAL_API_DATA_PATH', Defaults.PORTAL_API_DATA_PATH),
        dataspace=dataspace,
        token=os.getenv('PORTAL_API_KEY'),
        retries=retries
    )
    return ds
