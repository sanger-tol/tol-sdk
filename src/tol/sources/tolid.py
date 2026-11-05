# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .api import api
from .defaults import Defaults
from ..api_client import (
    ApiDataSource
)


def tolid(retries: int = 5, **kwargs) -> ApiDataSource:
    ds = api(
        url=os.getenv('TOLID_URL', Defaults.TOLID_URL),
        api_path=os.getenv('TOLID_API_PATH', Defaults.TOLID_API_PATH),
        api_data_path=os.getenv('TOLID_API_DATA_PATH', Defaults.TOLID_API_DATA_PATH),
        dataspace=None,
        token=os.getenv('TOLID_API_KEY'),
        retries=retries
    )
    return ds
