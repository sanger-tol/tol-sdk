# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter
    from ..session import OperableSession


class Statter(_Filterable, ABC):
    @abstractmethod
    def get_stats(
        self,
        object_type: str,
        stats_fields: List[str] = [],
        stats: List[str] = ['min', 'max'],
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> dict[Any, int]:
        """
        Gets stats for results that are matched by the (optional) filter
        """
