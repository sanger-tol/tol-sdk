# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

from tol.core import DataObject
from tol.dummy import create_dummy_datasource


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
    to_one: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    data_object._to_one_objects = to_one

    return data_object


class TestCreateDummyDatasource:
    """larger-than unit tests on `create_dummy_datasource`"""

    def test_get_by_id_record(self):
        """`create_dummy_datasource().get_by_id()` + no token"""

        dummy_ds = create_dummy_datasource()

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='record',
            id_=1
        )
        mock_do_factory.return_value = mock_data_object
        dummy_ds.data_object_factory = mock_do_factory

        observed = list(dummy_ds.get_by_id('record', [1]))
        assert observed == [mock_data_object]

    def test_get_by_id_multiple(self):
        """
        Multiple statuses, one of which is not found + token
        """

        api_ds = create_dummy_datasource()

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='record',
            id_=1
        )
        mock_do_factory.return_value = mock_data_object
        api_ds.data_object_factory = mock_do_factory

        observed = list(
            api_ds.get_by_id('record', [40404, 1])
        )
        assert observed == [None, mock_data_object]
