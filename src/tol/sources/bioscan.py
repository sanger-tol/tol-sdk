# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .api import api
from .defaults import Defaults


def bioscan(retries: int = 5, **kwargs) -> ApiDataSource:
    ds = api(
        url=os.getenv('BIOSCAN_URL', Defaults.BIOSCAN_URL),
        api_path=os.getenv('BIOSCAN_API_PATH', Defaults.BIOSCAN_API_PATH),
        api_data_path=os.getenv('BIOSCAN_API_DATA_PATH', Defaults.BIOSCAN_API_DATA_PATH),
        dataspace=None,
        token=os.getenv('BIOSCAN_API_KEY'),
        retries=retries
    )
    return ds
