# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .api import api
from .defaults import Defaults
from ..api_client import (
    ApiDataSource
)


def sts(
    retries: int = 5,
    status_forcelist: list[int] | None = [429, 500, 502, 503, 504]
) -> ApiDataSource:
    ds = api(
        url=os.getenv('STS_URL', Defaults.STS_URL),
        api_path=os.getenv('STS_API_PATH', Defaults.STS_API_PATH),
        api_data_path=os.getenv('STS_API_DATA_PATH', Defaults.STS_API_DATA_PATH),
        dataspace=None,
        token=os.getenv('STS_API_KEY'),
        retries=retries,
        status_forcelist=status_forcelist,
    )
    return ds
