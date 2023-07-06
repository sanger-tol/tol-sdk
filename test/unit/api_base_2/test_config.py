# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask_testing import TestCase

from tol.core import DataSource
from tol.core.operator import Relational
from tol.core.relationship import RelationshipConfig

from .app import _test_application


class Empty(DataSource):
    @property
    def supported_types(self):
        return [
            'know',
            'nothing'
        ]

    def get_attribute_types(self, object_type: str) -> dict:
        raise NotImplementedError()


class FirstRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return [
            'to_me',
            'to_you'
        ]

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        return {
            'to_me': RelationshipConfig(to_one={'barry': 'to_you'}),
            'to_you': RelationshipConfig(to_many={'paul': 'to_me'})
        }

    def get_attribute_types(self, object_type: str) -> dict:
        raise NotImplementedError()

    def get_to_many_relations(*args, **kwargs):
        raise NotImplementedError()

    def get_to_one_relation(*args, **kwargs):
        raise NotImplementedError()


class SecondRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return [
            'a',
            'b',
            'c',
            'd'  # no relationships to 'd'!
        ]

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        return {
            'a': RelationshipConfig(to_one={'easy': 'b', 'as': 'c'}),
            'b': RelationshipConfig(to_many={'jackson': 'a'}),
            'c': RelationshipConfig(to_many={'five': 'a'}),
            # this probably shouldn't happen, but better safe than sorry
            'd': RelationshipConfig()
        }

    def get_attribute_types(self, object_type: str) -> dict:
        raise NotImplementedError()

    def get_to_many_relations(*args, **kwargs):
        raise NotImplementedError()

    def get_to_one_relation(*args, **kwargs):
        raise NotImplementedError()


class TestConfigEmpty(TestCase):
    def create_app(self):
        return _test_application(Empty({}))

    def test_config_relationships_no_relational(self):
        """
        no relational `DataSource`s -> empty dict on config
        relationships endpoint
        """

        response = self.client.open('/data/_config/relationships')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        assert response.json == {}


class TestConfigPopulated(TestCase):
    def create_app(self):
        return _test_application(
            FirstRelational({}),
            SecondRelational({})
        )

    def test_config_relationships_with_relationals(self):
        """
        relational `DataSource`s -> (fully) populated dict
        on config relationships endpoint
        """

        response = self.client.open('/data/_config/relationships')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        assert response.json == {
            'to_me': {
                'one': {
                    'barry': 'to_you'
                }
            },
            'to_you': {
                'many': {
                    'paul': 'to_me'
                }
            },
            'a': {
                'one': {
                    'easy': 'b',
                    'as': 'c'
                },
            },
            'b': {
                'many': {
                    'jackson': 'a'
                },
            },
            'c': {
                'many': {
                    'five': 'a'
                }
            }
        }
