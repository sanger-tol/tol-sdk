# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client.filter import ApiFilterStrategy
from tol.core.datasource_filter import DataSourceFilter


class TestApiFilterStrategy:
    def test_converts_exact_filter_to_json_string(self):
        strategy = ApiFilterStrategy()
        f = DataSourceFilter(exact={'name': 'test'})

        result = strategy.convert('sample', f)

        assert '"exact"' in result
        assert '"name"' in result
        assert '"test"' in result

    def test_returns_none_for_none_filter(self):
        strategy = ApiFilterStrategy()
        assert strategy.convert('sample', None) is None

    def test_excludes_none_filter_fields(self):
        strategy = ApiFilterStrategy()
        f = DataSourceFilter(exact={'name': 'x'}, contains=None)

        result = strategy.convert('sample', f)

        assert 'contains' not in result

    def test_includes_and_filter(self):
        strategy = ApiFilterStrategy()
        f = DataSourceFilter(and_={
            'status': {'eq': {'value': 'active'}}
        })

        result = strategy.convert('sample', f)

        assert '"and_"' in result
        assert '"status"' in result

    def test_includes_range_filter(self):
        strategy = ApiFilterStrategy()
        f = DataSourceFilter(range={'age': {'from': 10, 'to': 20}})

        result = strategy.convert('sample', f)

        assert '"range"' in result
        assert '"age"' in result
