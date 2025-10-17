# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import Mock, PropertyMock, create_autospec

from flask import Flask

from flask_testing import TestCase

from tol.api_base.blueprint import _core_blueprint
from tol.api_client.view import DefaultView
from tol.core import DataSource, ReqFieldsTree
from tol.core.operator import DetailGetter, Relational
from tol.core.relationship import RelationshipConfig

# the relationship config
rc = RelationshipConfig(
    to_one={
        'first': 'yes',
        'second': 'another',
    },
    to_many={
        'ex': 'nihil',
        'nihil': 'fit',
    },
)

# Default requested fields tree for the "test" object type
test_req_flds_tree = ReqFieldsTree(
    'test',
    create_autospec(DataSource),
)


def mock_data_object(
    type_: str,
    id_: str | None = None,
    attributes: dict[str, Any] = None,
    host: DataSource | None = None,
    _related_objects: dict[str, Mock] = None,
) -> Mock:
    # mock the `DataObject`
    obj_mock = Mock(name='MockDataObj')
    # add relevant properties
    type(obj_mock).type = PropertyMock(return_value=type_)
    type(obj_mock).id = PropertyMock(return_value=id_)
    type(obj_mock).attributes = PropertyMock(
        return_value={} if attributes is None else attributes,
    )
    type(obj_mock)._host = PropertyMock(return_value=host)

    if _related_objects:
        if host:
            if rel_conf := host.relationship_config.get(type_):
                # Add properties containing the related objects
                type(obj_mock)._to_one_objects = _related_objects
                for name in rel_conf.to_one or ():
                    prop = PropertyMock(
                        return_value=_related_objects.get(name),
                    )
                    setattr(type(obj_mock), name, prop)
                for name in rel_conf.to_many or ():
                    prop = PropertyMock(
                        return_value=_related_objects.get(name, []),
                    )
                    setattr(type(obj_mock), name, prop)
            else:
                msg = f'{_related_objects = } but no relationship_config for {type_ = }'
                raise ValueError(msg)
        else:
            msg = f'{_related_objects = } but no host argument'
            raise ValueError(msg)

    return obj_mock


class _MockRelational(DataSource, DetailGetter, Relational):
    @property
    def supported_types(self) -> list[str]:
        return [
            'test',
            'bad',  # no relationship config
            'awful',  # config but no `to_one` or `to_many`
        ]

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        return {
            'test': rc,
            'awful': RelationshipConfig(),  # empty config
            'yes': RelationshipConfig(),
            'another': RelationshipConfig(),
        }

    def get_to_one_relation(*args, **kwargs):
        raise NotImplementedError()

    def get_to_many_relations(*args, **kwargs):
        raise NotImplementedError()

    def get_by_id(self, object_type: str, object_ids, **kwargs):
        assert len(object_ids) == 1
        return [
            mock_data_object(
                object_type,
                id_=object_ids[0],
                host=self,
                _related_objects={
                    'first': mock_data_object(
                        'yes',
                        '1234',
                        attributes={'attr1': 'val1'},
                    ),
                    'second': mock_data_object(
                        'another',
                        '5678',
                    ),
                },
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
            attributes={'int': 45980},
        )
        dump = DefaultView(test_req_flds_tree).dump(obj)
        expected = {
            'data': {
                'type': 'test',
                'id': '9606',
                'attributes': {'int': 45980},
            },
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
                attributes={'string': f'field_{i}'},
            )
            for i in range(5)
        ]
        dump = DefaultView(test_req_flds_tree).dump_bulk(objs)
        expected = {
            'data': [
                {
                    'type': 'test',
                    'id': str(i),
                    'attributes': {'string': f'field_{i}'},
                }
                for i in range(5)
            ]
        }
        assert dump == expected

    def test_relationships(self):
        """
        Dump with relationships. Doesn't include non set to_one objects
        """

        host = _MockRelational({})

        related_obj_mock = mock_data_object(
            'another',
            id_='5678',
            host=host,
        )

        obj_mock = mock_data_object(
            'test',
            id_='lol/abc',
            host=host,
            _related_objects={'second': related_obj_mock},
        )

        rv = ReqFieldsTree('test', host, include_all_to_ones=False)

        # the expected dumped output
        expected = {
            'data': {
                'type': 'test',
                'id': 'lol/abc',
                'relationships': {
                    'second': {'data': {'type': 'another', 'id': '5678'}},
                    'ex': {'links': {'related': '/random/test/lol%2Fabc/ex'}},
                    'nihil': {'links': {'related': '/random/test/lol%2Fabc/nihil'}},
                },
            }
        }
        dump = DefaultView(rv, prefix='/random').dump(obj_mock)
        assert dump == expected

    def test_hop_limit(self):
        """The `hop_limit` arg is obeyed if specified"""

        host = _MockRelational({})

        related_obj_mock = mock_data_object(
            'another',
            id_='5678',
            host=host,
            attributes={
                'rel_attr1': 'another1',
            },
        )

        obj_mock = mock_data_object(
            'test',
            id_='lol/abc',
            host=host,
            _related_objects={'second': related_obj_mock},
        )

        # the expected dumped output - doesn't include any to-ones
        expected = {
            'data': {
                'type': 'test',
                'id': 'lol/abc',
                'relationships': {
                    'second': {
                        'data': {
                            'type': 'another',
                            'id': '5678',
                            'attributes': {
                                'rel_attr1': 'another1',
                            },
                        },
                    },
                    'ex': {
                        'links': {
                            'related': '/random/test/lol%2Fabc/ex',
                        }
                    },
                    'nihil': {
                        'links': {
                            'related': '/random/test/lol%2Fabc/nihil',
                        }
                    },
                },
            }
        }
        view = DefaultView(
            ReqFieldsTree('test', host),
            prefix='/random',
            hop_limit=0,
        )
        dump = view.dump(obj_mock)
        assert dump == expected

    def test_meta(self):
        """Dump a single object with document meta"""
        obj = mock_data_object(
            'test',
            id_='pop3',
            attributes={'hype': 'train'},
        )
        meta = {
            'meta': 'you bet!',
            '2+2': '5',
        }
        expected = {
            'meta': meta,
            'data': {
                'type': 'test',
                'id': 'pop3',
                'attributes': {'hype': 'train'},
            },
        }
        observed = DefaultView(test_req_flds_tree).dump(obj, document_meta=meta)
        assert expected == observed

    def test_bulk_meta(self):
        """Dump many objects with document meta"""
        objs = [
            mock_data_object('test', id_=str(i), attributes={'hype': 'train'}) for i in range(50)
        ]
        meta = {
            'meta': 'you bet!',
            '2+2': '5',
        }
        expected = {
            'meta': meta,
            'data': [
                {
                    'type': 'test',
                    'id': str(i),
                    'attributes': {'hype': 'train'},
                }
                for i in range(50)
            ],
        }
        observed = DefaultView(test_req_flds_tree).dump_bulk(objs, document_meta=meta)
        assert expected == observed

    def test_no_relationship_config(self):
        """
        no `RelationshipConfig` is defined for the given type
        """

        mock_obj = mock_data_object(
            'bad',
            id_='lol',
            host=_MockRelational({}),
        )
        view = DefaultView(test_req_flds_tree)
        observed = view.dump(mock_obj)
        assert 'relationships' not in observed['data']

    def test_empty_relationship_config(self):
        """
        the `RelationshipConfig` for the given type is empty
        """

        mock_obj = mock_data_object(
            'awful',
            id_='lol',
            host=_MockRelational({}),
        )
        view = DefaultView(test_req_flds_tree)
        observed = view.dump(mock_obj)
        assert 'relationships' not in observed['data']


class TestDefaultViewInBlueprint(TestCase):
    """
    Tests the `DefaultView` within a data blueprint
    """

    def create_app(self):
        app = Flask(__name__)
        blueprint = _core_blueprint(
            {'test': _MockRelational({})},
            '/super_data',
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
            f'Response body is : {response.data.decode("utf-8")}',
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
                            'attributes': {
                                'attr1': 'val1',
                            },
                        },
                    },
                    'second': {
                        'data': {
                            'type': 'another',
                            'id': '5678',
                        },
                    },
                    'ex': {
                        'links': {
                            'related': '/super_data/test/hype/ex',
                        },
                    },
                    'nihil': {
                        'links': {
                            'related': '/super_data/test/hype/nihil',
                        }
                    },
                },
            }
        }
        observed = response.json
        assert observed == expected
