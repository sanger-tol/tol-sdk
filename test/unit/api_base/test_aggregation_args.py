# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base.misc import AggregationArgs
from tol.api_client.exception import BadPostJsonError


class TestAggregationArgs:
    def test_good_aggregations(self):
        """
        Instantiate every field that has a validation or requirement rule with valid data,
        and ensure that no exceptions were thrown
        """
        args = AggregationArgs(
            body_json={
                'x_axis': 'test_field',
                'date_interval': '2y',
            },
        )
        assert args.x_axis == 'test_field'
        assert args.date_interval == '2y'
