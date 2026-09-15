# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses

from tol.open_citations.client import OpenCitationsApiClient


FAKE_API_URL = 'http://test.lan/api'
FAKE_ACCESS_TOKEN = 'token'


class TestOpenCitationsApiClient:
    """The `OpenCitationsApiClient` and its methods."""

    @responses.activate
    def test_get_detail(self):
        """Default values."""

        client = OpenCitationsApiClient(FAKE_API_URL, FAKE_ACCESS_TOKEN)

        expected = [
            {
                'id': 'doi:10.1000/test-1',
                'title': 'First reference title',
            },
            {
                'id': 'doi:10.1000/test-2',
                'title': 'Second reference title',
            },
        ]
        responses.get(
            f'{FAKE_API_URL}/metadata/doi:10.1000/test-1__doi:10.1000/test-2',
            json=expected,
        )

        observed = client.get_detail('meta', ['10.1000/test-1', '10.1000/test-2'])

        assert observed == expected

    @responses.activate
    def test_get_detail_with_prefixed_identifier(self):
        """Preserves already-prefixed identifiers."""

        client = OpenCitationsApiClient(FAKE_API_URL)

        expected = [{'id': 'doi:10.1000/test'}]
        responses.get(
            f'{FAKE_API_URL}/metadata/doi:10.1000/test',
            json=expected,
        )

        observed = client.get_detail('meta', ['doi:10.1000/test'])

        assert observed == expected

    @responses.activate
    def test_get_detail_not_found(self):
        """404 response."""

        client = OpenCitationsApiClient(FAKE_API_URL)

        responses.get(
            f'{FAKE_API_URL}/metadata/doi:10.1000/missing',
            status=404,
            json={},
        )

        observed = client.get_detail('meta', ['10.1000/missing'])

        assert observed == []
