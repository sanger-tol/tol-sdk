# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..benchling import BenchlingDataSource
from .registry import default_registry


def benchling(**kwargs) -> BenchlingDataSource:
    return default_registry.create('benchling', **kwargs)
