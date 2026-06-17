# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import pytest

from tol.core import (
    DataObject,
    DataSourceError
)
from tol.dummy import DummyDataSource


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: Optional[dict[str, Any]] = None,
    to_one: Optional[dict[str, Any]] = None
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes or {}
    data_object.to_one = to_one or {}
    data_object._to_one_objects = to_one or {}

    return data_object


class TestDummyDataSource:
    def test_get_by_id_found_record(self):
        """200 response, no token"""

        mock_client = Mock()

        mock_response = {'id': 1, 'type': 'record', 'big_string': 'a'}
        mock_client.get_detail.return_value = [mock_response]

        mock_lc_converter = Mock()

        ds = DummyDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter
        )
        ds.data_object_factory = lambda: Mock()

        mock_data_object = _get_mock_data_object(
            type_='record',
            id_=1,
            attributes={'big_string': 'a'}
        )
        mock_lc_converter.convert_list.return_value = ([mock_data_object], 1)

        observed = list(ds.get_by_id('record', [1]))
        assert observed == [mock_data_object]

        mock_client.get_detail.assert_called_once_with(
            'record',
            [1]
        )
        mock_lc_converter.convert_list.assert_called_once_with(
            [mock_response]
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning `None`
        mock_client.get_detail.return_value = []

        mock_lc_converter = Mock()
        mock_lc_converter.convert_list.return_value = ([], None)

        ds = DummyDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter
        )
        ds.data_object_factory = lambda: Mock()

        observed = list(ds.get_by_id('record', [1]))
        assert observed == [None]

        mock_client.get_detail.assert_called_once_with(
            'record',
            [1]
        )
        mock_lc_converter.convert_list.assert_called_once_with(
            []
        )

    def test_bad_object_type(self):
        """A bad object type -> raise `DataSourceError()`"""

        ds = DummyDataSource(
            lambda: None,
            lambda: None
        )
        with pytest.raises(DataSourceError):
            list(ds.get_by_id('test', ['does not matter at all']))

    def test_supported_types(self):
        """
        `DummyDataSource().supported_types` calls
        `config_attribute_types()` on client
        """
        expected = ['record', 'category']

        ds = DummyDataSource(
            None,
            None
        )

        observed = ds.supported_types

        assert observed == expected
