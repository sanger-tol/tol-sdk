# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec, Mock

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


def mock_datasource(base_class: type = _AllDataSource) -> Mock:
    return create_autospec(base_class)
