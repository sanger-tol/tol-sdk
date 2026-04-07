# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from ..core import DataSourceFilter
from ..core.operator import AggregationResult


class ElasticAggregator(ABC):
    @abstractmethod
    def _field_or_keyword(self, object_type: str, name: str) -> str:
        """
        Helper method that maps fields in our format to Elastic's format. Implemented in the
        data source itself. This is defined as abstract here to indicate to other methods in this
        class that it'll be available.
        """
        raise NotImplementedError

    # This references the __get_elastic_aggregations method in ElasticDataSource. It must be
    # written this way here due to name mangling
    @abstractmethod
    def _ElasticDataSource__get_elastic_aggregations(
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
        elastic_response = self._ElasticDataSource__get_elastic_aggregations(
            object_type,
            {
                'aggs': {
                    'agg': {
                        'date_histogram': {
                            'field': x_axis,
                            'calendar_interval': date_interval,
                            'time_zone': 'Europe/London',
                        },
                    },
                },
            },
            object_filters,
        )

        # Parse to our response format
        return [
            {
                'key': None,
                'data': [
                    {
                        'x': data_point['key_as_string'],
                        'y': data_point['doc_count'],
                    }
                    for data_point in elastic_response['meta']['aggregations']['agg']['buckets']
                ]
            }
        ]

    def __get_date_aggregation_segmented(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        x_axis: str,
        date_interval: str,  # Validated in `AggregationArgs`
        break_down_by: str,
    ) -> AggregationResult:
        # Query Elastic
        elastic_response = self.__get_elastic_aggregations(
            object_type,
            {
                'aggs': {
                    'agg': {
                        'terms': {
                            'field': self._field_or_keyword(object_type, break_down_by),
                            'size': 25,
                        },
                        'aggs': {
                            '0': {
                                'date_histogram': {
                                    'field': x_axis,
                                    'calendar_interval': date_interval,
                                    'time_zone': 'Europe/London',
                                },
                            },
                        },
                    },
                },
            },
            object_filters,
        )

        # Parse to our response format
        return [
            {
                'key': str(break_down_by['key']),
                'data': [
                    {
                        'x': data_point['key_as_string'],
                        'y': data_point['doc_count']
                    }
                    # '1' is the key Elasticsearch returns for the nested aggregation
                    for data_point in break_down_by['1']['buckets']
                ]
            }
            for break_down_by in elastic_response['meta']['aggregations']['agg']['buckets']
        ]

    def __get_categorical_aggregation(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        x_axis: str,
        # TODO: This should only be used if x_axis is categorical. How do we know that?
        maximum_categories: int,
    ) -> AggregationResult:
        elastic_response = self.__get_elastic_aggregations(
            object_type,
            {
                'aggs': {
                    'agg': {
                        'terms': {
                            'field': self._field_or_keyword(object_type, x_axis),
                            'order': {
                                '_key': 'asc',
                            },
                            'size': 25,
                        },
                    },
                },
            },
            object_filters,
        )

        # Parse to our response format
        return [
            {
                'key': None,
                'data': [
                    {
                        'x': data_point['key'],
                        'y': data_point['doc_count'],
                    }
                    for data_point in elastic_response['meta']['aggregations']['agg']['buckets']
                ]
            }
        ]

    def __get_categorical_aggregation_segmented(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        x_axis: str,
        # TODO: This should only be used if x_axis is categorical. How do we know that?
        maximum_categories: int,
        break_down_by: str,
    ) -> AggregationResult:
        # Query Elastic
        elastic_response = self.__get_elastic_aggregations(
            object_type,
            {
                'aggs': {
                    'agg': {
                        'terms': {
                            'field': self._field_or_keyword(object_type, break_down_by),
                            'size': 25,
                        },
                        'aggs': {
                            '0': {
                                'terms': {
                                    'field': self._field_or_keyword(object_type, x_axis),
                                    'order': {
                                        '_key': 'asc',
                                    },
                                    'size': 25,
                                },
                            },
                        },
                    },
                },
            },
            object_filters,
        )

        # Parse to our response format
        return [
            {
                'key': str(break_down_by['key']),
                'data': [
                    {
                        'x': data_point['key'],
                        'y': data_point['doc_count']
                    }
                    # '1' is the key Elasticsearch returns for the nested aggregation
                    for data_point in break_down_by['1']['buckets']
                ]
            }
            for break_down_by in elastic_response['meta']['aggregations']['agg']['buckets']
        ]
