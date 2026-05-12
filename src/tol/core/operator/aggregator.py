# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter


AggregationResultData = list[dict]
AggregationResultKey = str | None
AggregationResultSegment = dict[str, AggregationResultKey | AggregationResultData]
AggregationResult = list[AggregationResultSegment]


class Aggregator(_Filterable, ABC):
    @abstractmethod
    def get_aggregations(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None,
        *,
        x_axis: str,
        y_axis: str | None = None,
        date_interval: str | None = None,
        break_down_by: str | None = None,
        stat: str | None = None,
        stat_field: str | None = None,
        cumulative: bool | None = None,
        maximum_categories: int | None = None,
    ) -> AggregationResult | None:
        """
        Returns a dictionary of aggregated data, or `None` if the options provided did not
        correspond to a valid aggregation
        """
