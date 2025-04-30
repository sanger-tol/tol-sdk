# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import create_autospec

from tol.api_client.view import DefaultView
from tol.core import DataObject


class TestViewRequestedFields:
    """
    `requested_fields` on `DefaultView`.
    """

    def test_no_hops(self) -> None:
        pass

    def test_two_hops(self) -> None:
        pass

    def __mock_object(
        self,
        sets: dict[str, Any]
    ) -> DataObject:

        obj: DataObject = create_autospec(DataObject)

        for k, v in sets.items():
            setattr(obj, k, v)

        return obj
