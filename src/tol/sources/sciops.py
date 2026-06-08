# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..sciops import SequencingDataSource
from .registry import default_registry


def sciops(**kwargs) -> SequencingDataSource:
    return default_registry.create('sciops', **kwargs)
