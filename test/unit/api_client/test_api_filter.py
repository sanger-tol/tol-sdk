# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client.filter import DefaultApiFilter
from tol.core import DataSourceFilter


class TestDefaultApiFilter:
    """Test the `DefaultApiFilter().dumps()` method"""

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
