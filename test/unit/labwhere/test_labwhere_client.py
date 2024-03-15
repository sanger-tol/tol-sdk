# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses

from tol.labwhere.client import LabwhereApiClient


FAKE_API_URL = 'http://test.lan/api'


class TestLabwhereApiClient:
    """The `LabwhereApiClient` and its methods"""

    @responses.activate
    def test_get_detail(self):
        """Default values, no token"""

        client = LabwhereApiClient(FAKE_API_URL)
        expected = {
            'name': 'test_name',
            'parentage': 'Root / Child1 / Child2'
        }

        responses.get(
            f'{FAKE_API_URL}/locations/hype',
            json=expected
        )

        observed = client.get_detail('location', 'hype')
        assert observed == expected
