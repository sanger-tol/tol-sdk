# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..mlwh import (
    MlwhDataSource
)


def mlwh(**kwargs) -> MlwhDataSource:
    mlwh = MlwhDataSource({'uri': os.getenv('MLWH_URI')})
    core_data_object(mlwh)
    return mlwh
