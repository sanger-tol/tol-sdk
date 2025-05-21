# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
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


def tolid(retries: int = 5, **kwargs) -> ApiDataSource:
    tolid = create_api_datasource(
        api_url=os.getenv('TOLID_URL', Defaults.TOLID_URL)
        + os.getenv('TOLID_API_PATH', Defaults.TOLID_API_PATH),
        token=os.getenv('TOLID_API_KEY'),
        data_prefix=os.getenv('TOLID_API_DATA_PATH', Defaults.TOLID_API_DATA_PATH),
        retries=retries
    )
    core_data_object(tolid)
    return tolid
