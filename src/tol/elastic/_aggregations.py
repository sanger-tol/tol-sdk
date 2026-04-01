from abc import ABC, abstractmethod

from ..core import DataSourceFilter
from ..core.operator import AggregationResult


class _ElasticAggregator(ABC):
    @abstractmethod
    def __get_elastic_aggregations(
        self,
        object_type: str,
        elastic_aggregations: dict,
        object_filters: DataSourceFilter | None = None,
    ) -> dict:
        """
        The helper method that makes the actual aggregations call to Elastic. Implemented in the
        data source itself. This is defined as abstract here to indicate to other methods in this
        class that it'll be available.
        """
        raise NotImplementedError

    def __get_date_aggregation(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        x_axis: str,
        date_interval: str,  # Validated in `AggregationArgs`
    ) -> AggregationResult:
        pass

    def __get_date_aggregation_segmented(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        x_axis: str,
        date_interval: str,  # Validated in `AggregationArgs`
        break_down_by: str,
    ) -> AggregationResult:
        pass

    def __get_categorical_aggregation(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        x_axis: str,
        # TODO: This should only be used if x_axis is categorical. How do we know that?
        maximum_categories: int,
    ) -> AggregationResult:
        pass

    def __get_categorical_aggregation_segmented(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        x_axis: str,
        # TODO: This should only be used if x_axis is categorical. How do we know that?
        maximum_categories: int,
        break_down_by: str,
    ) -> AggregationResult:
        pass
