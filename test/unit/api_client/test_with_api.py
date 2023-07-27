# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.api_base2 import data_blueprint
from tol.core import DataSource
from tol.core.operator import (
    Aggregator,
    Deleter,
    DetailGetter,
    PageGetter,
    Updater,
    Upserter
)


class _AllDataSource(
    DataSource,
    Aggregator,
    Deleter,
    DetailGetter,
    PageGetter,
    Updater,
    Upserter
):
    pass


create_autospec(_AllDataSource)


