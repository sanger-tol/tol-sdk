# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional

from tol.api_base2.parser import DefaultParser
from tol.core import DataObjectFactory


class TestDefaultParser:
    def test_no_attributes(self):
        """
        parse with no attributes (or relationships), just type and ID
        """

        in_ = {
            'type': 'test_lol',
            'id': 'hype'
        }
        factory = self.__factory_assert('test_lol', expected_id='hype')
        parser = DefaultParser(factory)
        parser.parse(in_)

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
        factory = self.__factory_assert(
            'whatever',
            expected_id='does_not_matter',
            expected_attributes={
                'float': 349.34,
                'int': 32984,
                'string': 'sdo8fd'
            }
        )
        parser = DefaultParser(factory)
        parser.parse(in_)

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
                'one': {
                    'excellent_relationship': {
                        'type': 'nice',
                        'id': 'idk'
                    }
                }
            }
        }
        factory = self.__factory_assert(
            'whatever',
            expected_id='does_not_matter',
            expected_attributes={
                'float': 349.34,
                'int': 32984,
                'string': 'sdo8fd'
            }
        )
        parser = DefaultParser(factory)
        parser.parse(in_)

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
                'id': '39845k'
            },
            {
                'type': 'test-the_third',
                'id': 'asdf8f',
                'attributes': {
                    'an_attr': True
                }
            }
        ]

        class _MockDataObject:
            def __init__(
                self,
                type_: str,
                id_: str,
                data: Optional[dict[str, Any]]
            ) -> None:

                self.type_ = type_
                self.id_ = id_
                self.attributes = data

        parser = DefaultParser(_MockDataObject)
        parsed = list(parser.parse_iterable(in_))

        assert parsed[0].type_ == 'test1'
        assert parsed[0].id_ == 'skdj8'
        assert parsed[0].attributes is None

        assert parsed[1].type_ == 'test_too'
        assert parsed[1].id_ == '39845k'
        assert parsed[1].attributes is None

        assert parsed[2].type_ == 'test-the_third'
        assert parsed[2].id_ == 'asdf8f'
        assert parsed[2].attributes == {
            'an_attr': True
        }

    def __factory_assert(
        self,
        expected_type: str,
        expected_id: Optional[str] = None,
        expected_attributes: Optional[dict[str, Any]] = None
    ) -> DataObjectFactory:
        """
        asserts that the args and kwargs given to the resulting
        `DataObjectFactory` mock are expected
        """

        def __inner(
            type_: str,
            id_: Optional[str] = None,
            data: Optional[dict[str, Any]] = None
        ) -> None:
            assert type_ == expected_type
            assert id_ == expected_id
            assert data == expected_attributes

        return __inner
