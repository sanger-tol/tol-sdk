# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from tol.core.datasource_filter import DataSourceFilter
from tol.elastic.filter import ElasticFilterStrategy


class TestElasticFilterStrategy:
    def test_converts_eq_to_match_query(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'eq': {'value': 'test'}}
        })
        result = strategy.convert('sample', f)

        assert {'match': {'name': 'test'}} in result['bool']['must']

    def test_converts_range_operators(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'age': {'gte': {'value': 18}}
        })
        result = strategy.convert('sample', f)

        assert {'range': {'age': {'gte': 18}}} in result['bool']['must']

    def test_negated_filter_goes_to_must_not(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'status': {'eq': {'value': 'deleted', 'negate': True}}
        })
        result = strategy.convert('sample', f)

        assert {'match': {'status': 'deleted'}} in result['bool']['must_not']

    def test_returns_empty_bool_for_none_filter(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        result = strategy.convert('sample', None)

        assert result == {'bool': {'must': [], 'must_not': []}}

    def test_uses_field_resolver_for_field_names(self):
        resolver = MagicMock(return_value='name.keyword')
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'eq': {'value': 'x'}}
        })
        strategy.convert('sample', f)

        resolver.assert_called_with('sample', 'name')

    def test_in_list_creates_terms_query(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'status': {'in_list': {'value': ['active', 'pending']}}
        })
        result = strategy.convert('sample', f)

        assert {'terms': {'status': ['active', 'pending'], 'boost': 1.0}} in result['bool']['must']

    def test_contains_creates_wildcard_query(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'contains': {'value': 'test'}}
        })
        result = strategy.convert('sample', f)

        assert {'wildcard': {'name': {'value': 'test*', 'boost': 1.0}}} in result['bool']['must']

    def test_exists_creates_exists_query(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'exists': {'value': True}}
        })
        result = strategy.convert('sample', f)

        assert {'exists': {'field': 'name'}} in result['bool']['must']

    def test_field_comparison_creates_script_filter(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'start_date': {'gt': {'field': 'end_date'}}
        })
        result = strategy.convert('sample', f)

        assert 'filter' in result['bool']
        assert 'script' in result['bool']['filter']
        
    def test_filter_value_empty(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'eq': {'value': ''}}
        })
        result = strategy.convert('sample', f)

        assert {'match': {'name': ''}} in result['bool']['must']
    
    def test_filter_value_null(self):
        resolver = lambda obj_type, field: field
        strategy = ElasticFilterStrategy(field_resolver=resolver)

        f = DataSourceFilter(and_={
            'name': {'eq': {'value': None}}
        })
        result = strategy.convert('sample', f)

        assert {'match': {'name': None}} in result['bool']['must']
