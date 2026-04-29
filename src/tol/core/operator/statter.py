# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter
    from ..session import OperableSession


class Statter(_Filterable, ABC):
    @abstractmethod
    def get_stats(
        self,
        object_type: str,
        stats_fields: list[str] = [],
        stats: list[str] = ['min', 'max'],
        object_filters: DataSourceFilter | None = None,
        session: OperableSession | None = None
    ) -> dict[str, dict[str, dict[str, int]]]:
        """
        Gets stats for results that are matched by the (optional) filter
        """
