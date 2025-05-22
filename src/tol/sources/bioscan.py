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


def bioscan(retries: int = 5, **kwargs) -> ApiDataSource:
    bioscan = create_api_datasource(
        api_url=os.getenv('BIOSCAN_URL', Defaults.BIOSCAN_URL)
        + os.getenv('BIOSCAN_API_PATH', Defaults.BIOSCAN_API_PATH),
        token=os.getenv('BIOSCAN_API_KEY'),
        data_prefix=os.getenv('BIOSCAN_API_DATA_PATH', Defaults.BIOSCAN_API_DATA_PATH),
        retries=retries
    )
    core_data_object(bioscan)
    return bioscan
