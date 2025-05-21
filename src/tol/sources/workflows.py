# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
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


def workflows(retries: int = 5, **kwargs) -> ApiDataSource:
    workflows = create_api_datasource(
        api_url=os.getenv('WORKFLOWS_URL', Defaults.WORKFLOWS_URL)
        + os.getenv('WORKFLOWS_API_PATH', Defaults.WORKFLOWS_API_PATH),
        token=os.getenv('WORKFLOWS_API_KEY'),
        data_prefix=os.getenv('WORKFLOWS_API_DATA_PATH', Defaults.WORKFLOWS_API_DATA_PATH),
        retries=retries
    )
    core_data_object(workflows)
    return workflows
