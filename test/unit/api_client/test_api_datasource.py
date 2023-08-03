# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

from tol.api_client import ApiDataSource
from tol.core.relationship import RelationshipConfig


class TestApiDataSource:
    def test_relationship_config(self):
        client = Mock()
        client.get_relationship_config.return_value = {
            'a': {
                'to_one': {
                    "ye 'ole B": 'b',
                    'the old man and the': 'c'
                }
            },
            'b': {
                'to_one': {
                    'the old man and the': 'c'
                },
                'to_many': {
                    "a's mine": 'a'
                }
            }
        }

        def __client_factory(url: str, key: str) -> Mock:
            """confirm the url and key are given"""

            assert url == 'http://fake.lan'
            assert key == 'key'

            return client

        api_ds = ApiDataSource(
            'http://fake.lan',
            'key',
            client_factory=lambda u, k: __client_factory(u, k) 
        )

        expected = {
            'a': RelationshipConfig(
                to_one={
                    "ye 'ole B": 'b',
                    'the old man and the': 'c'
                }
            ),
            'b': RelationshipConfig(
                to_one={
                    'the old man and the': 'c'
                },
                to_many={
                    "a's mine": 'a'
                }
            )
        }
        observed = api_ds.relationship_config

        assert observed == expected

    def test_supported_types(self):
        client = Mock()
        client.get_operations_config.return_value = {
            'a': {
                'noauth': ['upsert', 'delete']
            },
            'b': {
                'noauth': ['detailGet', 'pageGet']
            }
        }

        api_ds = ApiDataSource(
            'http://excellent.lan',
            'lol this is a key',
            client_factory=lambda __u, __k: client
        )

        expected = ['a', 'b']
        observed = api_ds.supported_types

        assert observed == expected

    def test_get_by_id(self):
        """A mixture of found and not founds"""

        ids = ['200, 301, 404']  # last is not found

        def __get_detail(
            type_: str,
            id_: str
        ) -> Optional[dict[str, Any]]:

            if id_ == '404':
                return None
            return {
                'type': type_,
                'id': id_,
                'attributes': {'mix': f'stuff_{type_}_{id_}'}
            }

        client = Mock()
        client.get_detail.side_effect = __get_detail

        parser = Mock()
        # parser doesn't do anything
        parser.convert_iterable.side_effect = lambda it: it

        api_ds = ApiDataSource(
            'http://excellent.lan',
            'lol this is a key',
            client_factory=lambda __u, __k: client,
            parser_factory=lambda __f: parser
        )

        expected = [
            {
                'type': 'http',
                'id': '200',
                'attributes': {'mix': 'stuff_http_200'}
            },
            {
                'type': 'http',
                'id': '301',
                'attributes': {'mix': 'stuff_http_301'}
            },
            None  # not found
        ]
        observed = list(
            api_ds.get_by_id('http', ids)
        )

        assert observed == expected
