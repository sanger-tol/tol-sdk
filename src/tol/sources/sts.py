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


def sts():
    sts = create_api_datasource(
        api_url=os.getenv('STS_URL') + os.getenv('STS_API_PATH'),
        token=os.getenv('STS_API_KEY'),
        data_prefix=os.getenv('STS_API_DATA_PATH', '')
    )
    core_data_object(sts)
    return sts
