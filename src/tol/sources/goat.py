# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..goat import (
    GoatDataSource,
    create_goat_datasource
)


def goat() -> GoatDataSource:
    goat = create_goat_datasource(
        goat_url=os.getenv('GOAT_URL') + os.getenv('GOAT_API_PATH'),
    )
    core_data_object(goat)
    return goat
