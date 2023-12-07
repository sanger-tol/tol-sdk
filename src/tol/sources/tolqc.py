# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from tol.api_client2 import (
    create_api_datasource
)
from tol.core import (
    core_data_object
)


def tolqc():
    tolqc = create_api_datasource(
        api_url=os.getenv('TOLQC_URL') + os.getenv('TOLQC_API_PATH'),
        token=os.getenv('TOLQC_API_KEY'),
        data_prefix=''
    )
    core_data_object(tolqc)
    return tolqc
