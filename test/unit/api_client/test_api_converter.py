# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

from tol.api_client.converter import DefaultObjectParser


class TestDefaultObjectParser:
    """
    Tests `DefaultObjectParser`
    """

    def test_convert(self):
        """the user-defined `DefaultObjectParser().convert`"""

        in_ = {
            'type': 'no_fun',
            'id': '890',
            'attributes': {
                'a': 'bc',
                'bool': True
            }
        }

        mock_object = Mock()

        def __mock_factory(type_, id_ = None, attributes = None):
            assert type_ == 'no_fun'
            assert id_ == '890'
            assert attributes == {
                'a': 'bc',
                'bool': True
            }
            return mock_object

        parser = DefaultObjectParser(__mock_factory)
        out_ = parser.convert(in_)

        assert out_ == mock_object
