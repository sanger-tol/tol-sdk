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
        api_url=os.getenv('PORTAL_URL') + os.getenv('PORTAL_API_PATH') + '/external/tolid',
        token=os.getenv('PORTAL_API_KEY'),
        data_prefix=''
    )
    core_data_object(tolid)
    return tolid
