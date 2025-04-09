# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Optional

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter
    from ..session import OperableSession


class Counter(_Filterable, ABC):
    """
    Counts number of results that match a filter
    """

    @abstractmethod
    def get_count(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> int:
        """
        Counts the number of results that are matched by the (optional) filter
        """
