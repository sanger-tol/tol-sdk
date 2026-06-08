# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..api_client import ApiDataSource
from .registry import default_registry


def tolqc(retries: int = 5, **kwargs) -> ApiDataSource:
    return default_registry.create('tolqc', retries=retries, **kwargs)
