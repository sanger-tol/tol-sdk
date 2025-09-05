# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..api_client import (
    ApiDataSource,
    create_api_datasource
)
from ..core import (
    core_data_object
)


def portal(
        retries: int = 5,
        dataspace: str = 'tol_production',
        **kwargs
) -> ApiDataSource:
    portal = create_api_datasource(
        api_url=os.getenv('PORTAL_URL', Defaults.PORTAL_URL)
        + os.getenv('PORTAL_API_PATH', Defaults.PORTAL_API_PATH),
        token=os.getenv('PORTAL_API_KEY'),
        data_prefix=os.getenv('PORTAL_API_DATA_PATH', Defaults.PORTAL_API_DATA_PATH)
        + f'/{dataspace}',
        retries=retries
    )
    core_data_object(portal)
    return portal
