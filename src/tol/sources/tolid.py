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


def tolid():
    tolid = create_api_datasource(
        api_url=os.getenv('TOLID_URL') + os.getenv('TOLID_API_PATH'),
        token=os.getenv('TOLID_API_KEY'),
        data_prefix=os.getenv('TOLID_API_DATA_PATH', '')
    )
    core_data_object(tolid)
    return tolid
