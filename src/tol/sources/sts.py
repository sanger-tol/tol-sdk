# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..api_client import ApiDataSource
from .registry import default_registry


def sts(
    retries: int = 5,
    status_forcelist: list[int] | None = [429, 500, 502, 503, 504]
) -> ApiDataSource:
    return default_registry.create(
        'sts', retries=retries, status_forcelist=status_forcelist
    )
