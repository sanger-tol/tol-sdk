# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

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
