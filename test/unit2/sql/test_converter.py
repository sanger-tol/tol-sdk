# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional

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

    @property
    def instance_id(self) -> Optional[str]:  # noqa
        return self.__id

    @property
    def instance_attributes(self) -> Dict[str, Any]:
        return self.__attributes


class TestDefaultConverter:
    def test_one_object_no_relationships(self):
        """One model no relationships"""

        attributes = {
            'hype': 'train',
            'meaningLife': 42.0
        }
        example = _ExampleModel(attributes, id_='909')
        converter = DefaultConverter(
            lambda e: f'{e.get_table_name()}s'
        )
        observed = list(converter.convert([example]))

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
            lambda e: f'{e.get_table_name()}s are the best'
        )
        observed = list(converter.convert(examples))

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
            lambda e: f'{e.get_table_name()}s are the best'
        )
        observed = converter.convert(examples)
        assert list(observed) == [None]
