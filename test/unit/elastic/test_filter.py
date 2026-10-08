# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

import pytest

from tol.core import DataSourceFilter
from tol.elastic import ElasticDataSource
from tol.elastic.filter import ElasticFilterConverter


class TestElasticFilter:
    @pytest.mark.parametrize('case_insensitive', [None, False, True])
    @pytest.mark.parametrize('match_anywhere', [None, False, True])
    @pytest.mark.parametrize('negate', [False, True])
    @pytest.mark.parametrize('values', [[], ['Abc', 'Def'], [5, True], ['Abc', 5, True]])
    def test_in_list_options(
        self, mock_elastic_data_source, case_insensitive, match_anywhere, negate, values
    ):
        constraint = {'value': values, 'negate': negate}
        if case_insensitive is not None:
            constraint['case_insensitive'] = case_insensitive
        if match_anywhere is not None:
            constraint['match_anywhere'] = match_anywhere
        filters = DataSourceFilter(and_={'field4': {'in_list': constraint}})
        if not values:
            clause = {'match_none': {}}
        elif not case_insensitive and not match_anywhere:
            clause = {'terms': {'field4.keyword': values, 'boost': 1.0}}
        else:
            alternatives = []
            for value in values:
                if isinstance(value, str) and match_anywhere:
                    alternatives.append({'wildcard': {'field4.keyword': {
                        'value': f'*{value}*',
                        'case_insensitive': bool(case_insensitive),
                        'boost': 1.0,
                    }}})
                elif isinstance(value, str) and case_insensitive:
                    alternatives.append({'term': {'field4.keyword': {
                        'value': value, 'case_insensitive': True
                    }}})
                else:
                    alternatives.append({'term': {'field4.keyword': {'value': value}}})
            clause = {'bool': {'should': alternatives, 'minimum_should_match': 1}}
        assert ElasticFilterConverter(mock_elastic_data_source).convert(
            'obj_type', filters
        ) == {'bool': {
            'must': [] if negate else [clause],
            'must_not': [clause] if negate else [],
        }}

    def test_in_list_literal_wildcards(self, mock_elastic_data_source):
        filters = DataSourceFilter(and_={'field4': {'in_list': {
            'value': [r'a*b?c\d'], 'match_anywhere': True
        }}})
        query = ElasticFilterConverter(mock_elastic_data_source).convert('obj_type', filters)
        assert query['bool']['must'] == [{'bool': {
            'should': [{'wildcard': {'field4.keyword': {
                'value': r'*a\*b\?c\\d*', 'case_insensitive': False, 'boost': 1.0
            }}}],
            'minimum_should_match': 1,
        }}]

    @pytest.mark.parametrize('case_insensitive', [None, False, True])
    @pytest.mark.parametrize('negate', [False, True])
    @pytest.mark.parametrize('value', ['Abc*?', 5, True])
    def test_eq_case_insensitive(
        self, mock_elastic_data_source, case_insensitive, negate, value
    ):
        constraint = {'value': value, 'negate': negate}
        if case_insensitive is not None:
            constraint['case_insensitive'] = case_insensitive
        field = 'field4' if isinstance(value, str) else 'field6'
        search_field = 'field4.keyword' if isinstance(value, str) else 'field6'
        filters = DataSourceFilter(and_={field: {'eq': constraint}})
        if case_insensitive and isinstance(value, str):
            clause = {'term': {search_field: {
                'value': value, 'case_insensitive': True
            }}}
        else:
            clause = {'match': {search_field: value}}
        assert ElasticFilterConverter(mock_elastic_data_source).convert(
            'obj_type', filters
        ) == {'bool': {
            'must': [] if negate else [clause],
            'must_not': [clause] if negate else [],
        }}

    @pytest.mark.parametrize('case_insensitive', [None, False, True])
    @pytest.mark.parametrize('match_anywhere', [None, False, True])
    @pytest.mark.parametrize('negate', [False, True])
    def test_contains_options(
        self, mock_elastic_data_source, case_insensitive, match_anywhere, negate
    ):
        constraint = {'value': 'Abc', 'negate': negate}
        if case_insensitive is not None:
            constraint['case_insensitive'] = case_insensitive
        if match_anywhere is not None:
            constraint['match_anywhere'] = match_anywhere
        object_filters = DataSourceFilter(
            and_={'field4': {'contains': constraint}},
        )
        clause = {'wildcard': {'field4.keyword': {
            'value': '*Abc*' if match_anywhere else 'Abc*',
            'case_insensitive': True if case_insensitive is None else case_insensitive,
            'boost': 1.0,
        }}}
        expected = {'bool': {
            'must': [] if negate else [clause],
            'must_not': [clause] if negate else [],
        }}
        assert ElasticFilterConverter(mock_elastic_data_source).convert(
            'obj_type', object_filters
        ) == expected

    def test_contains_literal_wildcards(self, mock_elastic_data_source):
        object_filters = DataSourceFilter(
            and_={'field4': {'contains': {
                'value': r'a*b?c\d', 'match_anywhere': True
            }}},
        )
        query = ElasticFilterConverter(mock_elastic_data_source).convert(
            'obj_type', object_filters
        )
        assert query['bool']['must'] == [{'wildcard': {'field4.keyword': {
            'value': r'*a\*b\?c\\d*',
            'case_insensitive': True,
            'boost': 1.0,
        }}}]

    def test_contains_options_are_per_constraint(self, mock_elastic_data_source):
        object_filters = DataSourceFilter(and_={
            'field1': {'contains': {
                'value': 'Abc', 'case_insensitive': False, 'match_anywhere': True
            }},
            'field4': {'contains': {'value': 'Def'}},
        })
        query = ElasticFilterConverter(mock_elastic_data_source).convert(
            'obj_type', object_filters
        )
        assert query['bool']['must'] == [
            {'wildcard': {'field1.keyword': {
                'value': '*Abc*', 'case_insensitive': False, 'boost': 1.0
            }}},
            {'wildcard': {'field4.keyword': {
                'value': 'Def*', 'case_insensitive': True, 'boost': 1.0
            }}},
        ]

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
                    {'wildcard': {'field4.keyword': {
                        'value': 'abc*', 'case_insensitive': True, 'boost': 1.0
                    }}},
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
