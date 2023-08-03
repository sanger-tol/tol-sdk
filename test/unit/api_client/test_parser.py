# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from tol.api_client.parser import DefaultParser


class TestDefaultParser:
    """
    Various tests for `DefaultParser`
    """

    def test_empty(self):
        """No attributes or relationships"""

        factory = MagicMock()
        parser = DefaultParser(factory)

        in_ = {
            'type': 'hello',
            'id': 'parser'
        }

        parser.convert(in_)

        factory.assert_called_once_with('type', 'hello', data=None)

    def test_attributes(self):
        """No relationships"""

        factory = MagicMock()
        parser = DefaultParser(factory)

        attributes = {
            'yes?': False,
            'why not?!': 'no'
        }
        in_ = {
            'type': 'hello',
            'id': 'parser',
            'attributes': attributes
        }

        parser.convert(in_)

        factory.assert_called_once_with(
            'type',
            'hello',
            data=attributes
        )

    def test_all(self):
        """Attributes and relationships"""

        factory = MagicMock()

        def __factory(type_, id_, data: dict = {}):
            # a kind of pseudo JSON:API dump

            one = data.pop('relation')
            return {
                'type': type_,
                'id': id_,
                'attributes': data,
                'relationships': {
                    'override': one
                }
            }

        factory.side_effect = __factory
        parser = DefaultParser(factory)

        attributes = {
            'yes?': False,
            'why not?!': 'no'
        }
        in_ = {
            'type': 'hello',
            'id': 'parser',
            'attributes': attributes,
            'relationships': {
                'relation': {
                    'data': {
                        'type': 'one',
                        'id': '1'
                    }
                }
            }
        }

        expected = {
            'type': 'hello',
            'id': 'parser',
            'attributes': attributes,
            'relationships': {
                'override': {
                    'data': {
                        'type': 'one',
                        'id': '1'
                    }
                }
            }
        }

        parser.convert(in_)

        observed = factory.assert_called_once_with(
            'type',
            'hello',
            data=attributes
        )
