# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..labwhere import LabwhereDataSource
from .registry import default_registry


def labwhere(**kwargs) -> LabwhereDataSource:
    return default_registry.create('labwhere', **kwargs)
