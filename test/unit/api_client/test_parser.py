# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional

from tol.api_client.parser import DefaultParser
from tol.core import DataObject, DataObjectFactory


class TestDefaultParser:
    """
    Various tests for `DefaultParser`
    """

    def test_empty(self):
        """No attributes or relationships"""

    def test_attributes(self):
        """No relationships"""

    def test_all(self):
        """Attributes and relationships"""

    def __get_factory(
        self,
        expected_type: str,
        expected_id: str,
        expected_attributes: Optional[dict[str, Any]] = {},
        expected_to_one_objects: Optional[dict[str, DataObject]] = {},
        return_value: Any = None
    ) -> DataObjectFactory:

        expected_data = expected_attributes | expected_to_one_objects

        def __factory(
            type_: str,
            id_: str,
            data: Optional[dict[str, Any]] = {}
        ) -> Any:

            assert type_ == expected_type
            assert id_ == expected_id
            assert data == expected_data

            return return_value

        return __factory
