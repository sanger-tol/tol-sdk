# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses

from tol.api_client.client import DefaultApiClient


class TestDefaultApiClient:
    """
    Tests `DefaultApiClient`, with outward calls mocked using
    `responses`.
    """

    def test_get_detail_existing(self):
        """
        `DefaultApiClient().get_detail()` calls out correctly with
        a GET method.
        """

    @responses.activate
    @responses.add(
        responses.GET,
        'http://api.lan/api/v1/data/',
        headers={
            
        }
    )
    def test_get_detail_not_found(self):
        """
        `DefaultApiClient().get_detail()` returns `None` on a 404
        """

    def test_get_page_empty(self):
        """
        `DefaultApiClient().get_page()` accepts an empty list.
        """

    def test_get_page_populated(self):
        """
        `DefaultApiClient().get_page()` accepts a pouplated list.
        """
