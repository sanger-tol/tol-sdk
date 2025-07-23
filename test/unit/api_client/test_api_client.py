# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses
from responses.matchers import (
    header_matcher,
    json_params_matcher,
    query_param_matcher
)

from tol.api_client.client import JsonApiClient


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

        sort_ = '-id'
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
    def test_get_count_complex(self):
        """`JsonApiClient().get_count` also with kwargs"""

        client = JsonApiClient(FAKE_API_URL, token='uplz')

        filter_ = 'this is totally random and unrealistic!!'

        expected = {'total': 17}

        expected_url = f'{FAKE_API_URL}/data/lol:count'
        responses.get(
            expected_url,
            json=expected,
            match=[
                query_param_matcher(
                    {
                        'filter': filter_
                    },
                    strict_match=True
                ),
                header_matcher({'token': 'uplz'})
            ]
        )

        observed = client.get_count(
            'lol',
            filter_string=filter_
        )
        assert observed == expected

    @responses.activate
    def test_get_stats_complex(self):
        """`JsonApiClient().get_stats` also with kwargs"""

        client = JsonApiClient(FAKE_API_URL, token='uplz')

        filter_ = 'this is totally random and unrealistic!!'

        expected = {
            'stats': {
                'field1_min': 2,
                'field1_max': 4,
                'field2_min': 3,
                'field2_max': 9
            }
        }
        expected_url = f'{FAKE_API_URL}/data/lol:stats'
        responses.get(
            expected_url,
            json=expected,
            match=[
                query_param_matcher(
                    {
                        'stats': 'min,max',
                        'stats_fields': 'field1,field2',
                        'filter': filter_
                    },
                    strict_match=True
                ),
                header_matcher({'token': 'uplz'})
            ]
        )

        observed = client.get_stats(
            'lol',
            stats_string='min,max',
            stats_fields_string='field1,field2',
            filter_string=filter_
        )
        assert observed == expected

    @responses.activate
    def test_delete(self):
        """`JsonApiClient().delete()`"""

        client = JsonApiClient(FAKE_API_URL, token='funds')
        expected_url = f'{FAKE_API_URL}/data/test/2%20and%20a%20bit'

        responses.delete(expected_url)

        client.delete('test', '2 and a bit')

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
            ],
            json={
                'data': []
            }
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

    @responses.activate
    def test_get_to_one_relation_recursive_200(self):
        """
        `Client().get_to_one_relation_recursive()` with a found
        result + token
        """

        expected = {
            'data': {
                'type': 'g',
                'id': 'a fun ID'
            }
        }

        client = JsonApiClient(FAKE_API_URL, token='yes')
        expected_url = (
            f'{FAKE_API_URL}/data/a:to-one/good_id/b/c/d/e/f/g'
        )

        responses.get(
            expected_url,
            json=expected,
            match=[
                header_matcher({'token': 'yes'}),
            ]
        )

        observed = client.get_to_one_relation_recursive(
            'a',
            'good_id',
            ['b', 'c', 'd', 'e', 'f', 'g']
        )

        assert observed == expected

    @responses.activate
    def test_get_to_one_relation_recursive_404(self):
        """
        `Client().get_to_one_relation_recursive()` but not found
        result + no token
        """

        client = JsonApiClient(FAKE_API_URL)
        expected_url = (
            f'{FAKE_API_URL}/data/a:to-one/good_id/b/c/d/e/f/g'
        )

        responses.get(expected_url, status=404)

        observed = client.get_to_one_relation_recursive(
            'a',
            'good_id',
            ['b', 'c', 'd', 'e', 'f', 'g']
        )

        assert observed is None

    @responses.activate
    def test_get_to_many_relations_page(self):
        """
        `Client().get_to_many_relations_page()` + token
        """

        expected = {
            'data': [
                {
                    'type': 'b',
                    'id': 'an id that is related'
                }
            ]
        }

        client = JsonApiClient(FAKE_API_URL, token='no :(')
        expected_url = (
            f'{FAKE_API_URL}/data/a:to-many/good_ideer/b_plural'
        )

        responses.get(
            expected_url,
            json=expected,
            match=(
                query_param_matcher(
                    {
                        'page': '9348',
                        'page_size': '1'
                    },
                    strict_match=True
                ),
                header_matcher({'token': 'no :('})
            )
        )

        observed = client.get_to_many_relations_page(
            'a',
            'good_ideer',
            'b_plural',
            9348,
            1
        )

        assert observed == expected

    @responses.activate
    def test_config_relationships(self):
        """
        `Client().config_relationships()` with token
        """

        expected = {
            'a': {
                'one': {
                    'bee movie': 'b'
                },
                'many': {
                    'high seas': 'c'
                }
            }
        }

        client = JsonApiClient(FAKE_API_URL, token='no :(')
        expected_url = (
            f'{FAKE_API_URL}/data/_config/relationships'
        )

        responses.get(
            expected_url,
            json=expected,
            match=[
                header_matcher({'token': 'no :('})
            ]
        )

        observed = client.config_relationships()

        assert observed == expected

    @responses.activate
    def test_get_session(self):
        """
        Fails 3 times, then succeeds
        """
        client = JsonApiClient(FAKE_API_URL, token='')

        for i in range(3):
            responses.add(
                responses.GET,
                f'{FAKE_API_URL}/data/test/hype',
                json={'error': 'Temporary failure'},
                status=503
            )

        responses.add(
            responses.GET,
            f'{FAKE_API_URL}/data/test/hype',
            json={'success': True},
            status=200
        )

        response = client.get_detail('test', 'hype')

        assert response == {'success': True}

    @responses.activate
    def test_get_funky_id(self):
        """
        Octothorps (`#`) and other funky characters
        are quoted in object_id
        """

        client = JsonApiClient(FAKE_API_URL, token='')

        responses.add(
            responses.GET,
            f'{FAKE_API_URL}/data/test:to-many/hype%23jank/relation?page=1&page_size=1',
            json={'success': True},
            status=200
        )

        response = client.get_to_many_relations_page(
            'test',
            'hype#jank',
            'relation',
            1,
            1,
        )

        assert response == {'success': True}
