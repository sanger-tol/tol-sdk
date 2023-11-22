# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses
from responses.matchers import (
    header_matcher,
    json_params_matcher,
    query_param_matcher
)

from tol.api_client2.client import JsonApiClient


FAKE_API_URL = 'http://test.lan/api/v1'


class TestJsonApiClient:
    """The `JsonApiClient` and its methods"""

    @responses.activate
    def test_get_detail(self):
        """Default values, no token"""

        client = JsonApiClient(FAKE_API_URL)
        expected = {'success': True}

        responses.get(
            f'{FAKE_API_URL}/data/test/hype',
            json=expected
        )

        observed = client.get_detail('test', 'hype')
        assert observed == expected

    @responses.activate
    def test_get_detail_404(self):
        """404 not found returns None + token usage"""

        client = JsonApiClient(FAKE_API_URL, token='abc')

        responses.get(
            f'{FAKE_API_URL}/data/test/hype',
            status=404,
            match=[
                header_matcher({'token': 'abc'}),
            ]
        )

        observed = client.get_detail('test', 'hype')
        assert observed is None

    @responses.activate
    def test_get_list_page_simple(self):
        """`JsonApiClient().get_list_page` with just args"""

        client = JsonApiClient(FAKE_API_URL)

        expected = {'data': [{'1': 1}, {'2': 2}]}
        responses.get(
            f'{FAKE_API_URL}/data/lol?page=1&page_size=20',
            json=expected
        )

        observed = client.get_list_page('lol', 1, 20)
        assert observed == expected

    @responses.activate
    def test_get_list_page_complex(self):
        """`JsonApiClient().get_list_page` also with kwargs"""

        client = JsonApiClient(FAKE_API_URL, token='uplz')

        sort_ = 'id-'
        filter_ = 'this is totally random and unrealistic!!'

        expected = {'data': [{'1': 1}, {'2': 2}]}
        expected_url = f'{FAKE_API_URL}/data/lol'
        responses.get(
            expected_url,
            json=expected,
            match=[
                query_param_matcher(
                    {
                        'page': '1',
                        'page_size': '20',
                        'filter': filter_,
                        'sort_by': sort_
                    },
                    strict_match=True
                ),
                header_matcher({'token': 'uplz'})
            ]
        )

        observed = client.get_list_page(
            'lol',
            1,
            20,
            filter_string=filter_,
            sort_string=sort_
        )
        assert observed == expected

    @responses.activate
    def test_delete(self):
        """`JsonApiClient().delete()`"""

        client = JsonApiClient(FAKE_API_URL, token='funds')
        expected_url = f'{FAKE_API_URL}/data/test/2'

        responses.delete(expected_url)

        client.delete('test', '2')

    @responses.activate
    def test_upsert(self):
        """`JsonApiClient().upsert()`"""

        transfer = {
            'data': [
                {
                    'type': 'test',
                    'id': str(i),
                    'attributes': {
                        'yes': True,
                        'no': i
                    }
                }
                for i in range(3)
            ]
        }

        client = JsonApiClient(FAKE_API_URL, token='funds')

        expected_url = f'{FAKE_API_URL}/data/test:upsert'
        responses.post(
            expected_url,
            match=[
                header_matcher({'token': 'funds'}),
                json_params_matcher(transfer, strict_match=True)
            ]
        )

        client.upsert('test', transfer)

    @responses.activate
    def test_config_operations(self):
        """`JsonApiClient().config_operations()`"""

        expected = {
            'thing1': {
                'noauth': ['aggregate', 'delete']
            },
            'thing2': {
                'noauth': ['listGet', 'upsert'],
                'auth': ['detailGet']
            }
        }

        client = JsonApiClient(FAKE_API_URL, token='puny')
        expected_url = f'{FAKE_API_URL}/data/_config/operations'

        responses.get(expected_url, json=expected)

        observed = client.config_operations()
        assert observed == expected

    @responses.activate
    def test_config_attribute_types(self):
        """`JsonApiClient().config_attribute_types()`"""

        expected = {
            'a': {
                '1': 'str',
                '2': 'int'
            },
            'b': {
                '3': 'bool'
            }
        }

        client = JsonApiClient(FAKE_API_URL, token='puny')
        expected_url = f'{FAKE_API_URL}/data/_config/attribute_types'

        responses.get(expected_url, json=expected)

        observed = client.config_attribute_types()
        assert observed == expected
