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
        os.getenv('TOLQC_URL') + os.getenv('TOLQC_API_PATH'),
        os.getenv('TOLQC_API_KEY')
    )
    core_data_object(tolqc)
    return tolqc
