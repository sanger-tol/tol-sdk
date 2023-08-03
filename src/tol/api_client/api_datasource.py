# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSource
from tol.core.operator import (
    Deleter,
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
)


class ApiDataSource(
    DataSource,
    Deleter,
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
):
    """
    Communicates with a remote API.
    """
