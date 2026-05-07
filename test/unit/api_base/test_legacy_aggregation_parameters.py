# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base.misc import LegacyAggregationParameters
from tol.api_client.exception import BadQueryArgError


class TestAggregationParameters:
    def test_no_parameters(self):
        """No page size or page key specified returns None"""
        parsed = LegacyAggregationParameters({'irrelevent': 'so?'})
        assert parsed.filter is None

    def test_good_filter(self):
        """Just filter, confirm that an integer is returned"""
        filter_string = """
            {"exact": {"column1": "value1"}}
        """
        parsed = LegacyAggregationParameters({'filter': filter_string})
        assert parsed.filter.exact == {'column1': 'value1'}

    def test_bad_filter(self):
        """non-JSON raises Exception"""
        for __val in ['0', 'sjdklsjd', '', ' ']:
            with pytest.raises(BadQueryArgError) as e:
                LegacyAggregationParameters({'filter': __val}).filter
            assert 'filter' in str(e.value)
            assert __val in str(e.value)
