# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import MagicMock, PropertyMock

from flask import Flask

from flask_testing import TestCase

from tol.api_base2.blueprint import _core_blueprint
from tol.api_client2.view import DefaultView
from tol.core import (
    DataObject,
    DataSource
)
from tol.core.operator import DetailGetter, Relational
from tol.core.relationship import RelationshipConfig

# the relationship config
rc = RelationshipConfig(
    to_one={
        'first': 'yes',
        'second': 'another'
    },
    to_many={
        'ex': 'nihilo',
        'nihil': 'fit'
    }
)


def mock_data_object(
    type_: str,
    id_: Optional[str] = None,
    attributes: dict[str, Any] = {},
    host: Optional[DataSource] = None
) -> MagicMock:

    # mock the `DataObject`
    obj_mock = MagicMock()
    # add relevant properties
    type(obj_mock).type = PropertyMock(return_value=type_)
    type(obj_mock).id = PropertyMock(return_value=id_)
    type(obj_mock).attributes = PropertyMock(
        return_value=attributes
    )
    type(obj_mock)._host = PropertyMock(return_value=host)

    return obj_mock


class _MockDataSource(DataSource, DetailGetter, Relational):
    @property
    def supported_types(self) -> list[str]:
        return [
            'test',
            'bad',  # no relationship config
            'awful'  # config but no `to_one` or `to_many`
        ]

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        return {
            'test': rc,
            'awful': RelationshipConfig()  # empty config
        }

    def get_to_one_relation(self, data_object: DataObject, key: str):
        if key == 'first':
            return mock_data_object('yes', '1234', attributes={'att1': 'val1'})
        if key == 'second':
            return mock_data_object('another', '5678')
        raise NotImplementedError()

    def get_to_many_relations(*args, **kwargs):
        raise NotImplementedError()

    def get_by_id(self, object_type: str, object_ids):
        assert len(object_ids) == 1
        return [
            mock_data_object(
                object_type,
                id_=object_ids[0],
                host=self
            )
        ]


class TestDefaultView:
    def test_dump_one_object(self):
        """
        Test dumping one object with no relationships
        """
        obj = mock_data_object(
            'test',
            id_='9606',
            attributes={
                'int': 45980
            }
        )
        dump = DefaultView().dump(obj)
        expected = {
            'data': {
                'type': 'test',
                'id': '9606',
                'attributes': {
                    'int': 45980
                }
            }
        }
        assert dump == expected

    def test_dump_many_objects(self):
        """
        Dump a list of objects with no relationships
        """
        objs = [
            mock_data_object(
                'test',
                id_=str(i),
                attributes={'string': f'field_{i}'}
            )
            for i in range(349)
        ]
        dump = DefaultView().dump_bulk(objs)
        expected = {
            'data': [
                {
                    'type': 'test',
                    'id': str(i),
                    'attributes': {
                        'string': f'field_{i}'
                    }
                }
                for i in range(349)
            ]
        }
        assert dump == expected

    def test_relationships(self):
        """Dump with relationships"""

        obj_mock = mock_data_object(
            'test',
            id_='lol/abc',
            host=_MockDataSource({})
        )

        # the expected dumped output
        expected = {
            'data': {
                'type': 'test',
                'id': 'lol/abc',
                'relationships': {
                    'first': {
                        'data': {
                            'type': 'yes',
                            'id': '1234',
                            'attributes': {'att1': 'val1'}
                        }
                    },
                    'second': {
                        'data': {
                            'type': 'another',
                            'id': '5678',
                            'attributes': {}
                        }
                    },
                    'ex': {
                        'links': {
                            'related': '/random/test/lol%2Fabc/ex'
                        }
                    },
                    'nihil': {
                        'links': {
                            'related': '/random/test/lol%2Fabc/nihil'
                        }
                    },
                }
            }
        }
        dump = DefaultView(prefix='/random').dump(obj_mock)
        assert dump == expected

    def test_meta(self):
        """Dump a single object with document meta"""
        obj = mock_data_object(
            'test',
            id_='pop3',
            attributes={'hype': 'train'}
        )
        meta = {
            'meta': 'you bet!',
            '2+2': '5'
        }
        expected = {
            'meta': meta,
            'data': {
                'type': 'test',
                'id': 'pop3',
                'attributes': {
                    'hype': 'train'
                }
            }
        }
        observed = DefaultView().dump(obj, document_meta=meta)
        assert expected == observed

    def test_bulk_meta(self):
        """Dump many objects with document meta"""
        objs = [
            mock_data_object(
                'test',
                id_=str(i),
                attributes={'hype': 'train'}
            )
            for i in range(50)
        ]
        meta = {
            'meta': 'you bet!',
            '2+2': '5'
        }
        expected = {
            'meta': meta,
            'data': [
                {
                    'type': 'test',
                    'id': str(i),
                    'attributes': {
                        'hype': 'train'
                    }
                }
                for i in range(50)
            ]
        }
        observed = DefaultView().dump_bulk(objs, document_meta=meta)
        assert expected == observed

    def test_no_relationship_config(self):
        """
        no `RelationshipConfig` is defined for the given type
        """

        mock_obj = mock_data_object(
            'bad',
            id_='lol',
            host=_MockDataSource({})
        )
        view = DefaultView()
        observed = view.dump(mock_obj)
        assert 'relationships' not in observed['data']

    def test_empty_relationship_config(self):
        """
        the `RelationshipConfig` for the given type is empty
        """

        mock_obj = mock_data_object(
            'awful',
            id_='lol',
            host=_MockDataSource({})
        )
        view = DefaultView()
        observed = view.dump(mock_obj)
        assert 'relationships' not in observed['data']


class TestDefaultViewInBlueprint(TestCase):
    """
    Tests the `DefaultView` within a data blueprint
    """

    def create_app(self):
        app = Flask(__name__)
        blueprint = _core_blueprint(
            {'test': _MockDataSource({})},
            '/super_data',
            lambda: None
        )
        app.register_blueprint(blueprint)
        return app

    def test_relationships(self):
        """
        relation links work, in a `DataBlueprint`
        """

        response = self.client.open('/super_data/test/hype')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        expected = {
            'data': {
                'type': 'test',
                'id': 'hype',
                'relationships': {
                    'first': {
                        'data': {
                            'type': 'yes',
                            'id': '1234',
                            'attributes': {'att1': 'val1'}
                        }
                    },
                    'second': {
                        'data': {
                            'type': 'another',
                            'id': '5678',
                            'attributes': {}
                        }
                    },
                    'ex': {
                        'links': {
                            'related': '/super_data/test/hype/ex'
                        }
                    },
                    'nihil': {
                        'links': {
                            'related': '/super_data/test/hype/nihil'
                        }
                    },
                }
            }
        }
        observed = response.json
        assert observed == expected
