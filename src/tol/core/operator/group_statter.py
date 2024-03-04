# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, List, Optional

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter


class GroupStatter(ABC):
    @abstractmethod
    def get_stats(
        self,
        object_type: str,
        group_by: List[str],
        stats_fields: List[str] = [],
        stats: List[str] = ['min', 'max'],
        object_filters: Optional[DataSourceFilter] = None
    ) -> dict[Any, int]:
        """
        Counts the number of results that are matched by the (optional) filter,
        broken down by the group_by parameter
        """
