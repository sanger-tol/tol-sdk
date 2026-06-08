# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..api_client import ApiDataSource
from .registry import default_registry


def workflows(retries: int = 5, **kwargs) -> ApiDataSource:
    return default_registry.create('workflows', retries=retries, **kwargs)
