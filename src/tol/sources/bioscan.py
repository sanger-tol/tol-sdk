# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..api_client2 import (
    create_api_datasource
)
from ..core import (
    core_data_object
)


def bioscan():
    bioscan = create_api_datasource(
        api_url=os.getenv('BIOSCAN_URL') + os.getenv('BIOSCAN_API_PATH'),
        token=os.getenv('BIOSCAN_API_KEY'),
        data_prefix=''
    )
    core_data_object(bioscan)
    return bioscan
