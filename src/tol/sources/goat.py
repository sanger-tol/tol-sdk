# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..goat import GoatDataSource
from .registry import default_registry


def goat(**kwargs) -> GoatDataSource:
    return default_registry.create('goat', **kwargs)
