# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

#TODO add adversarial tests between ApiDataSource and api_base2

import urllib.parse

import responses

from tol.api_client.client import DefaultApiClient


class TestDefaultApiClient:
    """
    Tests `DefaultApiClient`, with outward calls mocked using
    `responses`.
    """

    @responses.activate
    def test_get_detail_existing(self):
        """
        `DefaultApiClient().get_detail()` calls out correctly with
        a GET method, given an override data prefix.
        """

        expected = {
            'data': {
                'type': 'test',
                'id': 'found'
            }
        }

        responses.get(
            'http://api.lan/api/v1/data_override/test/found',
            headers={
                'Token': 'test-token'
            },
            json=expected
        )

        client = DefaultApiClient(
            'http://api.lan/api/v1',
            'test-token',
            # override the blueprint prefix
            data_prefix='data_override'
        )
        observed = client.get_detail('test', 'found')

        assert observed == expected

    @responses.activate
    def test_get_detail_not_found(self):
        """
        `DefaultApiClient().get_detail()` returns `None` on a 404
        """

        responses.get(
            'http://api.lan/api/v1/data/test/idk',
            headers={
                'Token': 'test-token'
            },
            status=404
        )

        client = DefaultApiClient(
            'http://api.lan/api/v1',
            'test-token'
        )
        observed = client.get_detail('test', 'idk')

        assert observed is None

    @responses.activate
    def test_get_page_empty(self):
        """
        `DefaultApiClient().get_page()` accepts an empty list.
        """

        responses.get(
            'http://api.lan/api/v1/data/test?page=1&page_size=2',
            headers={
                'Token': 'test-token'
            },
        )

        client = DefaultApiClient(
            'http://api.lan/api/v1',
            'test-token'
        )
        observed = client.get_page('test', 1, 2)

        assert observed is None

    @responses.activate
    def test_get_page_populated(self):
        """
        `DefaultApiClient().get_page()` accepts a pouplated list.
        """

    @responses.activate
    def test_get_page_kwargs(self):
        """
        The kwargs for `DefaultApiClient().get_page()` work:

        - sort_by
        - filters
        """
