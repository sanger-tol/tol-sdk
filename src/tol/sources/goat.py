# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..core import (
    core_data_object
)
from ..goat import (
    GoatDataSource,
    create_goat_datasource
)


def goat(**kwargs) -> GoatDataSource:
    goat = create_goat_datasource(
        goat_url=os.getenv('GOAT_URL', Defaults.GOAT_URL)
        + os.getenv('GOAT_API_PATH', Defaults.GOAT_API_PATH)
    )
    core_data_object(goat)
    return goat
