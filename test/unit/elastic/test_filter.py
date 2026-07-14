# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from tol.core import DataSourceFilter
from tol.elastic import ElasticDataSource
from tol.elastic.filter import ElasticFilterConverter


class TestElasticFilter:
    def test_build_query(self, mock_elastic_data_source: ElasticDataSource):
        # Check absent filters work
        expected = {'bool': {'must': [], 'must_not': []}}
        assert (
            expected == ElasticFilterConverter(mock_elastic_data_source).convert('obj_type', None)
        )

        # And filtering
        object_filters = DataSourceFilter()
        object_filters.and_ = {
            'field1': {
                'exists': {},
                'lt': {'field': 'field2'}
            },
            'field2': {
                'exists': {'negate': True}
            },
            'field3': {
                'lt': {'value': 16},
                'gte': {'value': 2}
            },
            'field4': {
                'contains': {'value': 'abc'}
            },
            'field5': {
                'in_list': {'value': ['one', 'two']}
            },
            'field6': {
                'eq': {'value': 5}
            },
            'field7': {
                'eq': {'value': 'haberdashery', 'negate': True}
            },
            'field8': {
                'gt': {'value': '2022-01-01'},
                'lte': {'value': '2023-01-01'}
            },
            'datefield': {
                'gt': {'value': '2022-01-01'},
                'lte': {'value': '2023-01-01'}
            },
            'relationship.field3': {
                'eq': {'value': 'string1'}
            }
        }
        filter_converter = ElasticFilterConverter(mock_elastic_data_source)
        expected = {
            'bool': {
                'must': [
                    {'exists': {'field': 'field1.keyword'}},
                    {'range': {'field3': {'lt': 16}}},
                    {'range': {'field3': {'gte': 2}}},
                    {'wildcard': {'field4.keyword': {'value': 'abc*', 'boost': 1.0}}},
                    {'terms': {'field5.value': ['one', 'two'], 'boost': 1.0}},  # provenanced
                    {'match': {'field6': 5}},
                    {'range': {'field8': {'gt': datetime(2022, 1, 1, 0, 0)}}},
                    {'range': {'field8': {'lte': datetime(2023, 1, 1, 0, 0)}}},
                    {'range': {'datefield': {'gt': datetime(2022, 1, 1, 0, 0)}}},
                    {'range': {'datefield': {'lte': datetime(2023, 1, 1, 0, 0)}}},
                    {'match': {'relationship.field3.keyword': 'string1'}}
                ],
                'must_not': [
                    {'exists': {'field': 'field2.keyword'}},
                    {'match': {'field7': 'haberdashery'}}
                ],
                'filter': filter_converter._get_field_comparison_filter(
                    'field1.keyword', 'field2.keyword', 'lt', False
                )
            }
        }

        assert expected == filter_converter.convert(
            'obj_type', object_filters
        )

    def test_build_query_relationship_id_runtime_field(
        self,
        mock_elastic_data_source: ElasticDataSource,
    ):
        mock_elastic_data_source.runtime_fields['obj_type']['relationship'] = {
            'type': 'keyword',
            'script': {
                'source': "emit('rel-1')"
            }
        }

        object_filters = DataSourceFilter()
        object_filters.and_ = {
            'relationship.id': {
                'eq': {'value': 'rel-1'}
            }
        }

        expected = {
            'bool': {
                'must': [
                    {'match': {'relationship.id.value': 'rel-1'}}
                ],
                'must_not': []
            }
        }

        assert expected == ElasticFilterConverter(mock_elastic_data_source).convert(
            'obj_type',
            object_filters,
        )
