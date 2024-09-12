# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..prefect import (
    PrefectDataSource,
    create_prefect_datasource
)


def prefect() -> PrefectDataSource:
    prefect = create_prefect_datasource(
        api_url=os.getenv('PREFECT_URL') + os.getenv('PREFECT_API_PATH')
    )
    core_data_object(prefect)
    return prefect
