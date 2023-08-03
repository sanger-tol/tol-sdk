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

    def __init__(
        self,
        url: str,
        key: str
    ) -> None:

        self.__url = url
        self.__key = key
