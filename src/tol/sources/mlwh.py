# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..mlwh import MlwhDataSource
from .registry import default_registry


def mlwh(**kwargs) -> MlwhDataSource:
    return default_registry.create('mlwh', **kwargs)
