# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter
from tol.jira.filter import DefaultJiraFilter


class TestDefaultJiraFilter:
    """Test the `DefaultApiFilter().dumps()` method"""

    def test_one_filter(self):
        """Just one filter term"""

        in_ = DataSourceFilter(
            and_={'a': {'eq': {'value': 'hello'}}, 'b': {'eq': {'value': 'yo'}}}
        )
        expected = 'a = "hello" AND b = "yo"'
        observed = DefaultJiraFilter({}).dumps(in_)
        assert expected == observed

    def test_all_filters(self):
        """Test all filter terms at once"""

        in_ = DataSourceFilter(
            and_={
                'a': {'eq': {'value': 'hello'}},
                'b': {'contains': {'value': 'hi'}},
                'c': {'in_list': {'value': ['1', '2', '3']}},
                'd': {'gt': {'value': '1'},
                      'lt': {'value': '2'}}
            }
        )
        expected = (
            'a = "hello" AND b ~ "hi" AND c in ("1","2","3") AND d < "2" AND d > "1"'
        )
        observed = DefaultJiraFilter({}).dumps(in_)
        assert expected == observed

    def test_field_mappings(self):
        """Test all filter terms at once"""

        in_ = DataSourceFilter(
            and_={
                'a': {'eq': {'value': 'hello'}},
                'b': {'contains': {'value': 'hi'}},
                'c': {'in_list': {'value': ['1', '2', '3']}},
                'd': {'gt': {'value': '1'},
                      'lt': {'value': '2'}},
                'user1.name': {'eq': {'value': 'My Name'}}
            }
        )
        field_mappings = {
            'customField1': {
                'system_name': 'a',
                'clause_name': 'cf1',
                'relation': None
            },
            'customField2': {
                'system_name': 'b',
                'clause_name': 'cf2',
                'relation': None
            },
            'customField3': {
                'system_name': 'c',
                'clause_name': 'cf3',
                'relation': None
            },
            'customField4': {
                'system_name': 'd',
                'clause_name': 'cf4',
                'relation': None
            },
            'relationField': {
                'system_name': 'e',
                'clause_name': 'user1',
                'relation': 'user'
            }
        }
        expected = (
            'cf1 = "hello" AND cf2 ~ "hi" AND cf3 in ("1","2","3") AND cf4 < "2" AND cf4 > "1" '
            'AND user1 = "My Name"'
        )
        observed = DefaultJiraFilter(field_mappings).dumps(in_)
        assert expected == observed
