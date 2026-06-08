# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..copo import CopoDataSource
from .registry import default_registry


def copo(**kwargs) -> CopoDataSource:
    return default_registry.create('copo', **kwargs)
