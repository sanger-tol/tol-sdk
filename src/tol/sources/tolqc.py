# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .api import api
from .defaults import Defaults


def tolqc(retries: int = 5, **kwargs) -> ApiDataSource:
    ds = api(
        url=os.getenv('TOLQC_URL', Defaults.TOLQC_URL),
        api_path=os.getenv('TOLQC_API_PATH', Defaults.TOLQC_API_PATH),
        api_data_path=os.getenv('TOLQC_API_DATA_PATH', Defaults.TOLQC_API_DATA_PATH),
        dataspace=None,
        token=os.getenv('TOLQC_API_KEY'),
        retries=retries
    )
    return ds
