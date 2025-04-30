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
        obj = self.__mock_object(
            'a',
            'AAAA',
            {
                'i_can_do': 'anything',
                'ignore_me': True,
            },
            {},
        )

        view = DefaultView(
            requested_fields=[
                'i_can_do'
            ]
        )

        dumped = view.dump(obj)

        assert 'i_can_do' in dumped['data']['attributes']
        assert 'ignore_me' not in dumped['data']['attributes']

    def test_two_hops(self) -> None:
        pass

    def __mock_object(
        self,
        type_: str,
        id_: str,
        attributes: dict[str, Any],
        ones: dict[str, DataObject],
    ) -> DataObject:

        obj: DataObject = create_autospec(DataObject)

        obj.type = type_
        obj.id = id_

        obj.attributes = attributes
        for k, v in attributes.items():
            setattr(obj, k, v)

        obj._to_one_objects = ones
        for k, v in ones.items():
            setattr(obj, k, v)

        return obj
