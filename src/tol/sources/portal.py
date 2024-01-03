# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..api_client2 import (
    ApiDataSource,
    create_api_datasource
)
from ..core import (
    core_data_object
)


def portal() -> ApiDataSource:
    portal = create_api_datasource(
        api_url=os.getenv('PORTAL_URL') + os.getenv('PORTAL_API_PATH'),
        token=os.getenv('PORTAL_API_KEY'),
        data_prefix=''
    )
    core_data_object(portal)
    return portal
