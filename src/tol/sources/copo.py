# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..copo import (
    CopoDataSource,
    create_copo_datasource
)
from ..core import (
    core_data_object
)


def copo(**kwargs) -> CopoDataSource:
    copo = create_copo_datasource(
        copo_url=os.getenv('COPO_URL', Defaults.COPO_URL)
        + os.getenv('COPO_API_PATH', Defaults.COPO_API_PATH)
    )
    core_data_object(copo)
    return copo
