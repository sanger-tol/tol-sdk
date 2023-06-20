# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base2.exception import BadQueryArgError
from tol.api_base2.misc import AggregationParameters


class TestAggregationParameters:
    def test_no_parameters(self):
        """No page size or page key specified returns None"""
        parsed = AggregationParameters({'irrelevent': 'so?'})
        assert parsed.filter is None

    def test_good_filter(self):
        """Just filter, confirm that an integer is returned"""
        filter_string = """
            {"exact": {"column1": "value1"}}
        """
        parsed = AggregationParameters({'filter': filter_string})
        assert parsed.filter.exact == {'column1': 'value1'}

    def test_bad_filter(self):
        """non-JSON raises Exception"""
        for __val in ['0', 'sjdklsjd', '', ' ']:
            with pytest.raises(BadQueryArgError) as e:
                AggregationParameters({'filter': __val}).filter
            assert 'filter' in str(e.value)
            assert __val in str(e.value)
