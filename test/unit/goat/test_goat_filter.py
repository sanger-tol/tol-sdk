# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter
from tol.goat.filter import DefaultGoatFilter


class TestDefaultGoatFilter:
    """Test the `DefaultGoatFilter().dumps()` method"""

    def test_one_filter(self):
        """Just one filter term"""

        in_ = DataSourceFilter(
            and_={'a': {'eq': {'value': 'hello'}}, 'b': {'eq': {'value': 'yo'}}}
        )
        expected = {
            'attributes': [
                {'name': 'a', 'operator': 'eq', 'value': 'hello'},
                {'name': 'b', 'operator': 'eq', 'value': 'yo'}
            ]
        }
        observed = DefaultGoatFilter().dumps(in_)
        assert expected == observed

    def test_all_filters(self):
        """Test all filter terms at once"""

        in_ = DataSourceFilter(
            and_={
                'a': {'eq': {'value': 'hello'}},
                'b': {'contains': {'value': 'hi'}},
                'c': {'in_list': {'value': ['1', '2', '3']}},
                'd': {'gt': {'value': '1'},
                      'lt': {'value': '2'}},
                'e': {'exists': {}},
                'f': {'eq': {'value': 'bye', 'negate': True}},
                'taxon_rank': {'eq': {'value': 'species'}},
            }
        )
        expected = {
            'attributes': [
                {'name': 'a', 'operator': 'eq', 'value': 'hello'},
                {'name': 'b', 'operator': 'eq', 'value': 'hi*'},
                {'name': 'c', 'operator': 'eq', 'value': ['1', '2', '3']},
                {'name': 'd', 'operator': 'lt', 'value': '2'},
                {'name': 'd', 'operator': 'gt', 'value': '1'},
                {'name': 'e', 'operator': 'exists'},
                {'name': 'f', 'operator': 'ne', 'value': 'bye'},
            ],
            'rank': 'species'
        }
        observed = DefaultGoatFilter().dumps(in_)
        assert expected == observed

    def test_taxa_filters(self):
        """id and scientific_name filters become taxa"""

        in_ = DataSourceFilter(
            and_={
                'id': {'in_list': {'value': ['9662', '9663']}},
                'scientific_name': {'eq': {'value': 'Meles meles'}},
            }
        )
        expected = {
            'taxa': ['9662', '9663', 'Meles meles']
        }
        observed = DefaultGoatFilter().dumps(in_)
        assert expected == observed
