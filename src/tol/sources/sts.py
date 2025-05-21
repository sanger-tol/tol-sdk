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


def sts(retries: int = 5, **kwargs) -> ApiDataSource:
    sts = create_api_datasource(
        api_url=os.getenv('STS_URL', Defaults.STS_URL)
        + os.getenv('STS_API_PATH', Defaults.STS_API_PATH),
        token=os.getenv('STS_API_KEY'),
        data_prefix=os.getenv('STS_API_DATA_PATH', Defaults.STS_API_DATA_PATH),
        retries=retries
    )
    core_data_object(sts)
    return sts
