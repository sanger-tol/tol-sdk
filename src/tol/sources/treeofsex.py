# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..api_client import ApiDataSource
from .registry import default_registry


def treeofsex(retries: int = 5, **kwargs) -> ApiDataSource:
    return default_registry.create('treeofsex', retries=retries, **kwargs)
