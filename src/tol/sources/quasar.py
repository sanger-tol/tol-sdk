# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
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


def quasar(retries: int = 5, **kwargs) -> ApiDataSource:
    quasar_ds = create_api_datasource(
        api_url=os.getenv('QUASAR_URL', Defaults.QUASAR_URL)
        + os.getenv('QUASAR_API_PATH', Defaults.QUASAR_API_PATH),
        token=os.getenv('QUASAR_API_KEY'),
        data_prefix=os.getenv('QUASAR_API_DATA_PATH', Defaults.QUASAR_API_DATA_PATH),
        retries=retries
    )
    core_data_object(quasar_ds)
    return quasar_ds
