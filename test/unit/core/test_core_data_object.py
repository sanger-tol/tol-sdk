# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, PropertyMock, create_autospec

import pytest

from tol.core import (
    DataSource,
    DataSourceError,
    core_data_object
)
from tol.core.operator import DetailGetter, Relational
from tol.core.relationship import RelationshipConfig


class _RelationalDS(DataSource, Relational):
    """A `DataSource` that implements `Relational`"""


class _DetailDS(DataSource, DetailGetter):
    """A `DataSource` that implements `Relational`"""


class TestCoreDataObject:
    """
    Tests the dunder methods of `CoreDataObject`:

    - `str`
    - `getattr`
    - `setattr`
    """

    def test_str_no_id(self):
        """`CoreDataObject().__str__` with no set `.id`"""

        mock_ds = create_autospec(DataSource)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject('test_type')

        assert 'type="test_type"' in str(obj)

    def test_str(self):
        """`CoreDataObject().__str__` with `.id`"""

        mock_ds = create_autospec(DataSource)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['type_too']
        )

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject('type_too', id_='lol')

        assert 'type="type_too"' in str(obj)
        assert 'id="lol"' in str(obj)

    def test_getattr_no_relationships(self):
        """
        `CoreDataObject().__getattr__` with just:

        - type
        - id
        - attributes
        """

        attributes = {
            'int': 42,
            'float': 23.9,
            'str': 'sdasid',
            'bool': True
        }

        mock_ds = create_autospec(DataSource)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        type(mock_ds).attribute_types = PropertyMock(
            return_value={c: c for c in attributes.keys()}
        )

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject(
            'test_type',
            id_='hype',
            attributes=attributes
        )

        assert obj.type == 'test_type'
        assert obj.id == 'hype'

        for k, v in attributes.items():
            assert getattr(obj, k) == v

    def test_getattr_to_one(self):
        """
        `CoreDataObject().__getattr__`, just:

        - type
        - id
        - _to_one_objects
        """

        mock_ds = create_autospec(_RelationalDS)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        type(mock_ds).relationship_config = {
            'test_type': RelationshipConfig(
                to_one={'enemy_mine': 'enemy'}
            )
        }

        mock_to_one = Mock()

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject(
            'test_type',
            id_='hype',
            to_one={'enemy_mine': mock_to_one}
        )

        assert obj.type == 'test_type'
        assert obj.id == 'hype'
        assert obj.enemy_mine == mock_to_one

    def test_getattr_get_unset(self):
        """
        `CoreDataObject().__getattr__` behaves correctly
        if value unset:

        - id                - returns None
        - attributes (key)  - returns None
        - to_one            - fetches using
                              `Relational().get_to_one_relation()`
        - to_many           - fetches an `Iterable` using
                              `Relational().get_to_many_relations()`
        """

        mock_to_one = Mock()
        mock_to_manys = [Mock() for _ in range(3)]

        mock_ds = create_autospec(_RelationalDS)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        type(mock_ds).attribute_types = PropertyMock(
            return_value={
                'test_type': {
                    'an_attr': 'str'
                }
            }
        )
        type(mock_ds).relationship_config = {
            'test_type': RelationshipConfig(
                to_one={'enemy_mine': 'enemy'},
                to_many={'friendos': 'friend'}
            )
        }
        mock_ds.get_to_one_relation.return_value = mock_to_one
        mock_ds.get_to_many_relations.return_value = mock_to_manys

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject('test_type')

        assert obj.id is None
        assert obj.an_attr is None

        to_manys = obj.enemy_mine
        mock_ds.get_to_one_relation.assert_called_once_with(
            obj,
            'enemy_mine'
        )
        assert to_manys == mock_to_one

        to_manys = list(obj.friendos)
        mock_ds.get_to_many_relations.assert_called_once_with(
            obj,
            'friendos'
        )
        assert to_manys == mock_to_manys

    def test_getattr_stub(self):
        """
        `CoreDataObject().__getattr__` behaves correctly
        if created as a stub:

        """

        mock_ds = create_autospec(_DetailDS)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        type(mock_ds).attribute_types = PropertyMock(
            return_value={
                'test_type': {
                    'an_attr': 'str'
                }
            }
        )

        CoreDataObject = core_data_object(mock_ds)  # noqa N806

        # This should fail with an exception as no ID set
        with pytest.raises(DataSourceError):
            obj = CoreDataObject('test_type', stub=True)

        # Set an ID and ensure that it gets real object from database (individual attribute)
        obj = CoreDataObject('test_type', 'id', stub=True)
        mock_ds.get_one.return_value = CoreDataObject(
            'test_type',
            id_='id',
            attributes={'an_attr': 'yes'}
        )
        assert obj.an_attr == 'yes'
        mock_ds.get_one.assert_called_once_with(
            'test_type',
            'id'
        )
        # Set an ID and ensure that it gets real object from database (attributes)
        mock_ds.get_one.reset_mock()
        obj = CoreDataObject('test_type', 'id2', stub=True)
        mock_ds.get_one.return_value = CoreDataObject(
            'test_type',
            id_='id2',
            attributes={'an_attr': 'yes'}
        )
        assert obj.attributes['an_attr'] == 'yes'
        mock_ds.get_one.assert_called_once_with(
            'test_type',
            'id2'
        )

    def test_setattr_attributes_and_id(self):
        """
        `CoreDataObject().__setattr__()` with just
        attributes and ID
        """

        mock_ds = create_autospec(DataSource)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        type(mock_ds).attribute_types = PropertyMock(
            return_value={}
        )

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject(
            'test_type',
            attributes={'yes': True}
        )

        assert obj.type == 'test_type'
        assert obj.id is None
        assert obj.attributes == {'yes': True}

        # override ID, and attributes (including yes key)
        obj.id = 'neverending hype'
        obj.yes = False
        obj.no = 3843
        obj.lol = '98ds9k'

        assert obj.type == 'test_type'
        assert obj.id == 'neverending hype'
        assert obj.attributes == {
            'yes': False,
            'no': 3843,
            'lol': '98ds9k'
        }

    def test_setattr_to_one_relationships(self):
        """
        `CoreDataObject().__setattr__()` with to_one
        relationship names -> set on
        `CoreDataObject()._to_one_objects`
        """

        mock_obj = Mock()
        mock_obj_override = Mock()

        mock_ds = create_autospec(_RelationalDS)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        type(mock_ds).attribute_types = PropertyMock(
            return_value={}
        )
        type(mock_ds).relationship_config = {
            'test_type': RelationshipConfig(
                to_one={'enemy_mine': 'enemy'}
            )
        }

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject(
            'test_type',
            to_one={'enemy_mine': mock_obj}
        )

        first_observed = obj.enemy_mine
        mock_ds.get_to_one_relation.assert_not_called()
        assert first_observed == mock_obj

        # set the object again
        obj.enemy_mine = mock_obj_override

        # confirm its changed
        second_observed = obj.enemy_mine
        mock_ds.get_to_one_relation.assert_not_called()
        assert second_observed == mock_obj_override

    def test_setattr_to_many_relationships(self):
        """
        `CoreDataObject().__setattr__()` with to_many
        relationship names -> `DataSourceError` raised
        (this is not permitted by design)
        """

        mock_ds = create_autospec(_RelationalDS)
        type(mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        type(mock_ds).attribute_types = PropertyMock(
            return_value={}
        )
        type(mock_ds).relationship_config = {
            'test_type': RelationshipConfig(
                to_many={'friendos': 'friend'}
            )
        }

        CoreDataObject = core_data_object(mock_ds)  # noqa N806
        obj = CoreDataObject('test_type')

        with pytest.raises(DataSourceError):
            obj.friendos = [Mock()]
