# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..api_client import ApiDataSource
from .defaults import Defaults
from .registry import default_registry


def portal(
        retries: int = 5,
        dataspace: str = 'tol_production',
        **kwargs
) -> ApiDataSource:
    data_prefix = (
        os.getenv('PORTAL_API_DATA_PATH', Defaults.PORTAL_API_DATA_PATH)
        + f'/{dataspace}'
    )
    return default_registry.create(
        'portal', retries=retries, data_prefix=data_prefix, **kwargs
    )
