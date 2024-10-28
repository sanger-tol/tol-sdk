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


def bioscan():
    bioscan = create_api_datasource(
        api_url=os.getenv('BIOSCAN_URL', Defaults.BIOSCAN_URL)
        + os.getenv('BIOSCAN_API_PATH', Defaults.BIOSCAN_API_PATH),
        token=os.getenv('BIOSCAN_API_KEY'),
        data_prefix=os.getenv('BIOSCAN_API_DATA_PATH', Defaults.BIOSCAN_API_DATA_PATH)
    )
    core_data_object(bioscan)
    return bioscan
