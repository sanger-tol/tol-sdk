# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base.misc import AggregationArgs
from tol.api_client.exception import PostJsonInvalidValueError, PostJsonKeyMissingError


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
    
    def test_required_fields_not_provided(self):
        REQUIRED_FIELDS = ('x_axis',)
        
        args = AggregationArgs({})
        for required_field in REQUIRED_FIELDS:
            # Ensure attempting to get the required field raises an error
            with pytest.raises(PostJsonKeyMissingError) as e:
                getattr(args, required_field)

            # Ensure the correct error was raised (the required field was mentioned)
            assert required_field in str(e.value)

    def test_invalid_date_interval(self):
        """
        `date_interval` should be formatted as a number followed by an accepted unit (e.g. 1M)
        """
        # Invalid format
        with pytest.raises(PostJsonInvalidValueError) as e:
            AggregationArgs({'date_interval': '1 month'}).date_interval
        assert 'Invalid format' in e.value.errors[0]['detail']

        # Invalid unit
        with pytest.raises(PostJsonInvalidValueError) as e:
            AggregationArgs({'date_interval': '1m'}).date_interval
        assert 'Invalid unit' in e.value.errors[0]['detail']
