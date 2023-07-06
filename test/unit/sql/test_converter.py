# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Iterable, Optional

from tol.core import DataObject
from tol.sql.converter import DefaultConverter
from tol.sql.model import Model


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
        pass

    @classmethod
    def get_to_one_relationship_config(cls):
        pass

    @property
    def instance_to_one_relations(self) -> dict[str, Optional[Model]]:
        pass

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
    def host(self) -> None:
        raise NotImplementedError()

    @property
    def _to_one_objects(self) -> None:
        raise NotImplementedError()


def factory(type_, id_=None, data=None):
    return _ExampleDataObject(type_, id_, data)


class TestDefaultConverter:
    def test_one_object_no_relationships(self):
        """One model no relationships"""

        attributes = {
            'hype': 'train',
            'meaningLife': 42.0
        }
        example = _ExampleModel(attributes, id_='909')
        converter = DefaultConverter(lambda e: f'{e.get_table_name()}s', factory)
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
        converter = DefaultConverter(
            lambda e: f'{e.get_table_name()}s are the best',
            factory
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
        converter = DefaultConverter(
            lambda e: f'{e.get_table_name()}s are the best',
            factory
        )
        observed = converter.convert_iterable(examples)
        assert list(observed) == [None]
