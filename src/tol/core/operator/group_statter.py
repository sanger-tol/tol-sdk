# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter
    from ..session import OperableSession


class GroupStatter(_Filterable, ABC):
    @abstractmethod
    def get_group_stats(
        self,
        object_type: str,
        group_by: list[str],
        stats_fields: list[str] = [],
        stats: list[str] = ['min', 'max'],
        object_filters: DataSourceFilter | None = None,
        session: OperableSession | None = None
    ) -> Iterable[dict[str, dict[str, int | dict[str, int]]]]:
        """
        Gets stats for results that are matched by the (optional) filter,
        broken down by the group_by parameter
        """
