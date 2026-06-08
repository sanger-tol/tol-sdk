# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..sts import StsDataSource
from .registry import default_registry


def sts_legacy(**kwargs) -> StsDataSource:
    return default_registry.create('sts_legacy', **kwargs)
