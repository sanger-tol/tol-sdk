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


def sts():
    sts = create_api_datasource(
        os.getenv('PORTAL_URL') + os.getenv('PORTAL_API_PATH') + '/external/sts',
        os.getenv('PORTAL_API_KEY')
    )
    core_data_object(sts)
    return sts
