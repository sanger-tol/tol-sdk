# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base.misc import LegacyAggregationBody
from tol.api_client.exception import PostJsonKeyMissingError


class TestAggregationBody:
    def test_no_aggregations(self):
        """No aggregations specified throws error"""
        with pytest.raises(PostJsonKeyMissingError):
            LegacyAggregationBody({'irrelevent': 'so?'}).aggs

    def test_good_aggregations(self):
        """Just aggregations, confirm that an integer is returned"""
        agg = {'something': 'here'}
        parsed = LegacyAggregationBody({'aggs': agg})
        assert parsed.aggs == {'something': 'here'}
