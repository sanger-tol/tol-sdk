# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock, PropertyMock, create_autospec

from tol.api_client.parser import DefaultParser
from tol.core import DataObject, DataSource


class TestDefaultParser:
    def test_no_attributes(self):
        """
        parse with no attributes (or relationships), just type and ID
        """

        in_ = {
            'type': 'test_lol',
            'id': 'hype'
        }
        parser = DefaultParser(
            {'test_lol': self.__mock_data_source()}
        )
        parsed = parser.parse(in_)

        assert parsed.id == 'hype'
        assert parsed.type == 'test_lol'
        assert not parsed.attributes
        assert not parsed._to_one_objects

    def test_no_relationships(self):
        """
        parse with no relationships, just attributes, type, and ID
        """

        in_ = {
            'type': 'whatever',
            'id': 'does_not_matter',
            'attributes': {
                'float': 349.34,
                'int': 32984,
                'string': 'sdo8fd'
            }
        }
        parser = DefaultParser(
            {'whatever': self.__mock_data_source()}
        )
        parsed = parser.parse(in_)

        assert parsed.type == 'whatever'
        assert parsed.id == 'does_not_matter'
        assert parsed.attributes == {
            'float': 349.34,
            'int': 32984,
            'string': 'sdo8fd'
        }

    def test_full_resource(self):
        """
        test with all members.

        N.B. - currently just _ignores_ relationships
        """

        in_ = {
            'type': 'whatever',
            'id': 'does_not_matter',
            'attributes': {
                'float': 349.34,
                'int': 32984,
                'string': 'sdo8fd'
            },
            'relationships': {
                'excellent_relationship': {
                    'data': {
                        'type': 'nice',
                        'id': 'idk'
                    }
                }
            }
        }
        ds = self.__mock_data_source()
        parser = DefaultParser(
            {
                'nice': ds,
                'whatever': ds
            }
        )
        parsed = parser.parse(in_)

        assert parsed.type == 'whatever'
        assert parsed.id == 'does_not_matter'
        assert parsed.attributes == {
            'float': 349.34,
            'int': 32984,
            'string': 'sdo8fd'
        }

        to_ones = parsed._to_one_objects
        assert to_ones is not None
        assert len(to_ones) == 1

        the_one = to_ones['excellent_relationship']
        assert the_one.type == 'nice'
        assert the_one.id == 'idk'
        assert not the_one.attributes
        assert not the_one._to_one_objects

    def test_parse_iterable(self):
        """
        a full document parsing of three resources
        """

        in_ = [
            {
                'type': 'test1',
                'id': 'skdj8'
            },
            {
                'type': 'test_too',
                'id': '39845k',
                'relationships': {
                    'he_is_the_one': {
                        'data': {
                            'type': 'neo',
                            'id': '1999'
                        }
                    }
                }
            },
            {
                'type': 'test-the_third',
                'id': 'asdf8f',
                'attributes': {
                    'an_attr': True
                }
            }
        ]

        mock_ds = self.__mock_data_source()
        parser = DefaultParser(
            {
                'test1': mock_ds,
                'test_too': mock_ds,
                'test-the_third': mock_ds,
                'neo': mock_ds
            }
        )
        parsed = list(parser.parse_iterable(in_))

        assert parsed[0].type == 'test1'
        assert parsed[0].id == 'skdj8'
        assert not parsed[0].attributes
        assert not parsed[0]._to_one_objects

        assert parsed[1].type == 'test_too'
        assert parsed[1].id == '39845k'
        assert not parsed[1].attributes
        one_to_ones = parsed[1]._to_one_objects
        assert one_to_ones is not None
        assert len(one_to_ones) == 1
        the_one = one_to_ones['he_is_the_one']
        assert the_one.type == 'neo'
        assert the_one.id == '1999'
        assert not the_one.attributes
        assert not the_one._to_one_objects

        assert parsed[2].type == 'test-the_third'
        assert parsed[2].id == 'asdf8f'
        assert parsed[2].attributes == {
            'an_attr': True
        }
        assert not parsed[2]._to_one_objects

    def test_both_relationships(self):
        """Many relationships are ignored."""
        data = {
            'type': 'test_too',
            'id': '39845k',
            'relationships': {
                'he_is_the_one': {
                    'data': {
                        'type': 'neo',
                        'id': '1999'
                    }
                },
                'entirely_too_many': {
                    'data': [
                        {
                            'type': 'eep',
                            'id': str(i)
                        }
                        for i in range(7)
                    ]
                },
                'yet_another_one_relationship': {
                    'data': {
                        'type': 'lol',
                        'id': 'also lol'
                    }
                }
            }
        }

        mock_ds = self.__mock_data_source()
        parser = DefaultParser(
            {
                'test_too': mock_ds,
                'epp': mock_ds,
                'lol': mock_ds,
                'neo': mock_ds
            }
        )
        parsed = parser.parse(data)

        assert parsed.type == 'test_too'
        assert parsed.id == '39845k'
        assert not parsed.attributes

        to_ones = parsed._to_one_objects
        assert to_ones is not None
        assert len(to_ones) == 2

        first = to_ones['he_is_the_one']
        assert first.type == 'neo'
        assert first.id == '1999'
        assert not first.attributes
        assert not first._to_one_objects

        first = to_ones['yet_another_one_relationship']
        assert first.type == 'lol'
        assert first.id == 'also lol'
        assert not first.attributes
        assert not first._to_one_objects

    def __mock_data_source(self) -> Mock:
        mock_ds = create_autospec(DataSource, spec_set=True)

        type(mock_ds).data_object_factory = PropertyMock(
            return_value=self.__mock_factory
        )

        return mock_ds

    def __mock_factory(
        self,
        type_: str,
        id_: Optional[str] = None,
        attributes: dict[str, Any] = {},
        to_one: dict[str, Any] = {},
        to_many: dict[str, Any] = {}
    ) -> Mock:

        mock_obj = create_autospec(DataObject, spec_set=True)

        type(mock_obj).type = PropertyMock(return_value=type_)
        type(mock_obj).id = PropertyMock(return_value=id_)
        type(mock_obj).attributes = PropertyMock(return_value=attributes)
        type(mock_obj)._to_one_objects = PropertyMock(return_value=to_one)

        assert not to_many

        return mock_obj
