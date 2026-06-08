# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..bold import BoldDataSource
from .registry import default_registry


def bold(**kwargs) -> BoldDataSource:
    return default_registry.create('bold', **kwargs)
