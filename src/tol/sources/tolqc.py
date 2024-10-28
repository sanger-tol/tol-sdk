# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..api_client2 import (
    create_api_datasource
)
from ..core import (
    core_data_object
)


def tolqc():
    tolqc = create_api_datasource(
        api_url=os.getenv('TOLQC_URL', Defaults.TOLQC_URL)
        + os.getenv('TOLQC_API_PATH', Defaults.TOLQC_API_PATH),
        token=os.getenv('TOLQC_API_KEY'),
        data_prefix=os.getenv('TOLQC_API_DATA_PATH', Defaults.TOLQC_API_DATA_PATH)
    )
    core_data_object(tolqc)
    return tolqc
