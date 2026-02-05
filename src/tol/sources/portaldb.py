# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..api_client import (
    ApiDataSource,
    create_api_datasource
)
from ..core import (
    core_data_object
)


def portaldb(retries: int = 5, **kwargs) -> ApiDataSource:
    portaldb = create_api_datasource(
        api_url=os.getenv('PORTAL_URL') + os.getenv('PORTAL_API_PATH') + '/local',
        token=os.getenv('PORTAL_API_KEY'),
        data_prefix='',
        retries=retries
    )
    core_data_object(portaldb)
    return portaldb
