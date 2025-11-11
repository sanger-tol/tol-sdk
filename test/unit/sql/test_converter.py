# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Iterable, Optional
from unittest.mock import MagicMock, Mock, PropertyMock

from tol.core import Converter, DataObject, ReqFieldsTree
from tol.sql.model import Model
from tol.sql.sql_converter import (
    DefaultDataObjectConverter,
    DefaultModelConverter
)


class _ExampleModel(Model):
    def __init__(
        self,
        attributes: Dict[str, Any],
        id_: Optional[str] = None
    ) -> None:

        self.__attributes = attributes
        self.__id = id_

    @classmethod
    def get_table_name(cls) -> str:
        return 'test'

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id'

    @classmethod
    def get_column(cls, name: str):
        pass

    @classmethod
    def get_to_many_relationship_config(cls):
        return {}

    @classmethod
    def get_to_one_relationship_config(cls):
        return {}

    @classmethod
    def get_foreign_key_name(cls, relationship_name: str) -> str:
        raise NotImplementedError()

    @classmethod
    def get_attribute_types(cls) -> dict[str, type]:
        raise NotImplementedError()

    @property
    def instance_to_one_relations(self) -> dict[str, Optional[Model]]:
        return {}

    @property
    def instance_to_many_relations(self) -> dict[str, Iterable[Model]]:
        pass

    @property
    def instance_id(self) -> Optional[str]:  # noqa
        return self.__id

    @property
    def instance_attributes(self) -> Dict[str, Any]:
        return self.__attributes


class _ExampleDataObject(DataObject):
    def __init__(self, type_, id_=None, data_=None):
        self.__type = type_
        self.__id = id_
        self.__data = data_

    @property
    def id(self):  # noqa
        return self.__id

    @property
    def attributes(self):
        return self.__data

    @property
    def type(self):  # noqa
        return self.__type

    @property
    def to_many_relationships(self):
        return {}

    @property
    def to_one_relationships(self):
        return {}

    @property
    def _host(self) -> None:
        raise NotImplementedError()

    @property
    def _to_one_objects(self) -> None:
        raise NotImplementedError()


def tests_req_fields_tree():
    return ReqFieldsTree('tests', Mock(), include_all_to_ones=False)


def factory(type_, id_=None, attributes=None, to_one=None, to_many=None):
    return _ExampleDataObject(type_, id_, attributes)


class _IsEvenConverter(Converter[int, bool]):
    """
    Converts evens to `True`, odds to `False`
    """

    def convert(self, input_: int) -> bool:
        return input_ % 2 == 0


class TestConverter:
    def test_convert_optional_none(self):
        """`None` input does not call `convert()`"""

        converter = _IsEvenConverter()
        assert converter.convert_optional(None) is None

    def test_convert_optional_not_none(self):
        """a not `None` input does call `convert()`"""

        converter = _IsEvenConverter()
        assert converter.convert_optional(2) is True

    def test_convert_iterable(self):
        """
        an iterable of mixed `None` and not-`None` inputs
        calls `convert()` appropriately
        """

        # a bit like fizzbuzz, None if a multiple of 4
        inputs = [
            i if i % 4 != 0 else None
            for i in range(60)
        ]
        expected = [None, False, True, False] * 15  # 60=15*4
        converter = _IsEvenConverter()
        observed = list(converter.convert_iterable(inputs))

        assert observed == expected


class TestDefaultModelConverter:
    def test_one_object_no_relationships(self):
        """One model no relationships"""

        attributes = {
            'hype': 'train',
            'meaningLife': 42.0
        }
        example = _ExampleModel(attributes, id_='909')
        rft = tests_req_fields_tree()
        converter = DefaultModelConverter(lambda e: f'{e.get_table_name()}s', factory, rft)
        observed = list(converter.convert_iterable([example]))

        assert len(observed) == 1
        first = list(observed)[0]

        assert first.id == '909'
        assert first.type == 'tests'
        assert first.attributes == attributes

    def test_several_objects_no_relationships(self):
        """Several objects no relationships"""

        examples = [
            _ExampleModel(
                {
                    'i_think': f'therefore I A{"A" * 2 * i}M',
                    'this': 'the way'
                }
            )
            for i in range(9)
        ]
        rft = tests_req_fields_tree()
        converter = DefaultModelConverter(
            lambda e: f'{e.get_table_name()}s are the best',
            factory,
            rft,
        )
        observed = list(converter.convert_iterable(examples))

        assert len(observed) == 9

        for i, data_object in enumerate(observed):
            assert data_object.type == 'tests are the best'
            assert data_object.id is None
            assert data_object.attributes == {
                'i_think': f'therefore I A{"A" * 2 * i}M',
                'this': 'the way'
            }

    def test_none_model(self):
        """Converting None returns None"""

        examples = [None]
        rft = tests_req_fields_tree()
        converter = DefaultModelConverter(
            lambda e: f'{e.get_table_name()}s are the best',
            factory,
            rft,
        )
        observed = converter.convert_iterable(examples)
        assert list(observed) == [None]


class TestDefaultDataObjectConverter:
    def test_no_attributes_or_relationships(self):
        """A single `DataObject` with just type and ID"""

        mock_object = self.__create_mock_object('tests', 'lol')
        mock_model_class = self.__create_mock_object_class()

        converter = DefaultDataObjectConverter(
            {'tests': mock_model_class}
        )
        converter.convert(mock_object)

        mock_model_class.assert_called_once_with(id='lol')

    def test_override_id_column_name(self):
        """`Model.get_id_column_name()` is used and respected"""

        mock_object = self.__create_mock_object('tests', 'lol')
        mock_model_class = self.__create_mock_object_class(
            id_column_name='epic_override'
        )

        converter = DefaultDataObjectConverter(
            {'tests': mock_model_class}
        )
        converter.convert(mock_object)

        mock_model_class.assert_called_once_with(
            epic_override='lol'
        )

    def test_attributes(self):
        """
        A single `DataObject` with type, ID, and attributes
        """

        attributes = {
            'one': 'ksdjskadjl',
            'bool': True,
            'yet_another': 890345
        }

        mock_object = self.__create_mock_object(
            'tests',
            'lol',
            attributes=attributes
        )
        mock_model_class = self.__create_mock_object_class()

        converter = DefaultDataObjectConverter(
            {'tests': mock_model_class}
        )
        converter.convert(mock_object)

        mock_model_class.assert_called_once_with(
            id='lol',
            **attributes
        )

    def test_to_one_relationship(self):
        """
        A single `DataObject` with type, ID, and a single
        to-one relationship
        """

        mock_relation_object = self.__create_mock_object(
            'relation',
            'rel'
        )
        mock_object = self.__create_mock_object(
            'tests',
            'lol',
            ones={'one_happy_family': mock_relation_object}
        )
        mock_model_class = self.__create_mock_object_class(
            # relationship name is `one_happy_family`
            # foreign key name is `indeed` (its value is `'rel'`)
            foreign_key_map={'one_happy_family': 'indeed_foreign_key'}
        )
        mock_relation_class = MagicMock()
        mock_relation_class.get_id_column_name.return_value = 'id_hyped_up'
        mock_relation_class.return_value = mock_relation_class
        mock_relation_class.attributes = {}
        mock_relation_class._to_one_objects = {}

        converter = DefaultDataObjectConverter(
            {
                'tests': mock_model_class,
                'relation': mock_relation_class
            }
        )
        converter.convert(mock_object)

        mock_model_class.assert_called_once_with(
            id='lol',
            indeed_foreign_key='rel'
        )

    def __create_mock_object(
        self,
        type_: str,
        id_: str,
        attributes: dict[str, Any] = {},
        ones: dict[str, Any] = {}
    ) -> MagicMock:

        mock_object = MagicMock()
        type(mock_object).type = PropertyMock(return_value=type_)
        type(mock_object).id = PropertyMock(return_value=id_)
        type(mock_object).attributes = PropertyMock(
            return_value=attributes
        )
        type(mock_object)._to_one_objects = PropertyMock(
            return_value=ones
        )

        return mock_object

    def __create_mock_object_class(
        self,
        id_column_name: str = 'id',
        foreign_key_map: dict[str, str] = {}
    ) -> MagicMock:

        mock_model_class = MagicMock()
        mock_model_class.get_id_column_name.return_value = id_column_name
        mock_model_class.get_foreign_key_name.side_effect = (
            lambda r_name: foreign_key_map[r_name]
        )

        return mock_model_class
