# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..ena import EnaDataSource
from .registry import default_registry


def ena(**kwargs) -> EnaDataSource:
    return default_registry.create('ena', **kwargs)
