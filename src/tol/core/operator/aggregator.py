# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod

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
        date_interval: str | None = None,
        break_down_by: str | None = None,
        stat: str | None = None,
        stat_field: str | None = None,
        cumulative: bool | None = None,
        maximum_categories: int | None = None,
    ) -> dict:
        return {'hey': 'there'}
    
    @abstractmethod
    def get_date_bar_chart_aggregation(
        self,
        x_axis: str,
        date_interval: str,
        break_down_by: str | None,
        stat: str | None,
        stat_field: str | None,
        cumulative: bool,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_categorical_bar_chart_aggregation(
        self,
        x_axis: str,
        break_down_by: str | None,
        stat: str | None,
        stat_field: str | None,
        maximum_categories: int,
    ) -> dict:
        raise NotImplementedError

    def get_scatter_plot_aggregation(
        self,
        x_axis: str,
        y_axis: str,
        break_down_by: str | None,
    ) -> dict:
        # TODO: This is concrete and should be implemented here
        raise NotImplementedError

