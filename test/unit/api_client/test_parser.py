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

    def test_all(self):
        """Attributes and relationships"""
