# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter
from tol.ena.filter import DefaultEnaFilter


class TestDefaultEnaFilter:
    """Test the `DefaultEnaFilter().dumps method"""

    def test_one_filter(self):
        """Just one filter term"""

        in_ = DataSourceFilter(
            and_={'a': {'eq': {'value': 'hello'}}, 'b': {'eq': {'value': 'world'}}}
        )
        expected = 'a=hello AND b=world'
        observed = DefaultEnaFilter().dumps(in_)
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
            }
        )
        expected = (
            'a=hello AND b=hi* AND c="1" OR c="2" OR c="3" AND d<2 AND d>1'
        )
        observed = DefaultEnaFilter().dumps(in_)
        assert expected == observed
