# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter


class Aggregator(_Filterable, ABC):
    def get_aggregations(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None,
        *,
        x_axis: str | None = None,
        y_axis: str | None = None,
        break_down_by: str | None = None,
        stat: str | None = None,
        stat_field: str | None = None,
        cumulative: bool | None = None,
        maximum_categories: int | None = None,
    ) -> dict:
        return {'hey': 'there'}
