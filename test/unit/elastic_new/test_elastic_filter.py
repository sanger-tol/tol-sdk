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
        expected = 'a=hello AND b=yo'
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
                'taxon_rank': {'eq': {'value': 'species'}},
            }
        )
        expected = (
            'a=hello AND b=hi* AND c=1,2,3 AND d<2 AND d>1 AND tax_rank(species)'
        )
        observed = DefaultGoatFilter().dumps(in_)
        assert expected == observed
