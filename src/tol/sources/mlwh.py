# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from tol.core import (
    core_data_object
)
from tol.mlwh import (
    MlwhDataSource
)


def mlwh():
    mlwh = MlwhDataSource({'uri': os.getenv('MLWH_URI')})
    core_data_object(mlwh)
    return mlwh
