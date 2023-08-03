# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import Mock, PropertyMock

from tol.api_client.dumper import DefaultDumper
from tol.core import DataObject


class TestDefaultDumper:
    """
    Various tests for `DefaultDumper`
    """

    def test_empty(self):
        """No attributes or relationships"""

    def test_attributes(self):
        """No relationships"""

    def test_all(self):
        """Attributes and relationships"""

    def __mock_object(
        self,
        type_: str,
        id_: str,
        attributes: dict[str, Any] = {},
        to_one_objects: dict[str, DataObject] = {}
    ) -> Mock:

        mock_object = Mock()
        type(mock_object).type = PropertyMock(return_value=type_)
        type(mock_object).id = PropertyMock(return_value=id_)
        type(mock_object).attributes = PropertyMock(
            return_value=attributes
        )
        type(mock_object)._to_one_objects = PropertyMock(
            return_value=to_one_objects
        )
