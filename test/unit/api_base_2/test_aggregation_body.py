# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base2.exception import BadPostJsonError
from tol.api_base2.misc import AggregationBody


class TestAggregationBody:
    def test_no_aggregations(self):
        """No aggregations specified throws error"""
        with pytest.raises(BadPostJsonError):
            AggregationBody({'irrelevent': 'so?'}).aggs

    def test_good_aggregations(self):
        """Just aggregations, confirm that an integer is returned"""
        agg = {'something': 'here'}
        parsed = AggregationBody({'aggs': agg})
        assert parsed.aggs == {'something': 'here'}
