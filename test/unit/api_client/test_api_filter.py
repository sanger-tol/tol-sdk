# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from json import loads

import pytest

from tol.api_client.filter import DefaultApiFilter
from tol.core import DataSourceFilter


class TestDefaultApiFilter:
    """Test the `DefaultApiFilter().dumps()` method"""

    @pytest.mark.parametrize('case_insensitive', [False, True])
    @pytest.mark.parametrize('match_anywhere', [False, True])
    def test_in_list_options(self, case_insensitive, match_anywhere):
        constraint = {
            'value': ['abc', 'def'],
            'case_insensitive': case_insensitive,
            'match_anywhere': match_anywhere,
        }
        filters = DataSourceFilter(and_={'name': {'in_list': constraint}})
        assert loads(DefaultApiFilter().dumps(filters)) == {
            'and_': {'name': {'in_list': constraint}}
        }

    @pytest.mark.parametrize('case_insensitive', [False, True])
    def test_eq_case_insensitive(self, case_insensitive):
        constraint = {'value': 'abc', 'case_insensitive': case_insensitive}
        filters = DataSourceFilter(and_={'name': {'eq': constraint}})
        assert loads(DefaultApiFilter().dumps(filters)) == {
            'and_': {'name': {'eq': constraint}}
        }

    @pytest.mark.parametrize('case_insensitive', [False, True])
    @pytest.mark.parametrize('match_anywhere', [False, True])
    def test_contains_options(self, case_insensitive, match_anywhere):
        constraint = {
            'value': 'abc',
            'case_insensitive': case_insensitive,
            'match_anywhere': match_anywhere,
        }
        in_ = DataSourceFilter(
            and_={'name': {'contains': constraint}},
        )
        assert loads(DefaultApiFilter().dumps(in_)) == {
            'and_': {'name': {'contains': constraint}},
        }

    def test_one_filter(self):
        """Just one filter term"""

        in_ = DataSourceFilter(exact={'a': True, 'b': 'yo'})
        expected = '{"exact":{"a":true,"b":"yo"}}'
        observed = DefaultApiFilter().dumps(in_)
        assert expected == observed

    def test_all_filters(self):
        """Test all filter terms at once"""

        in_ = DataSourceFilter(
            exact={'a': True},
            contains={'b': 'hi'},
            in_list={'c': ['1', '2', '3']},
            range={'d': {'from': '1', 'to': '2'}}
        )
        expected = (
            '{"exact":{"a":true},'
            '"contains":{"b":"hi"},'
            '"in_list":{"c":["1","2","3"]},'
            '"range":{"d":{"from":"1","to":"2"}}}'
        )
        observed = DefaultApiFilter().dumps(in_)
        assert expected == observed
