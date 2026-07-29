# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import pytest

from tol.core import DataObject, DataSourceError
from tol.open_citations import OpenCitationsDataSource


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
) -> DataObject:

    data_object = Mock()
    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    return data_object


class TestOpenCitationsDataSource:
    def test_get_by_id_found(self):
        """200 response."""

        mock_client = Mock()
        mock_client.get_detail.return_value = [{'id': 'doi:10.1000/test'}]

        mock_converter = Mock()

        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )
        ds.data_object_factory = lambda: Mock()

        mock_data_object = _get_mock_data_object(
            type_='meta',
            id_='10.1000/test',
        )
        mock_converter.convert_list.return_value = ([mock_data_object], 1)

        observed = list(ds.get_by_id('meta', ['10.1000/test']))

        assert observed == [mock_data_object]
        mock_client.get_detail.assert_called_once_with('meta', ['10.1000/test'])
        mock_converter.convert_list.assert_called_once_with(
            'meta',
            [{'id': 'doi:10.1000/test'}],
        )

    def test_get_by_id_not_found(self):
        """404 response."""

        mock_client = Mock()
        mock_client.get_detail.return_value = []

        mock_converter = Mock()
        mock_converter.convert_list.return_value = ([], 0)

        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('meta', ['10.1000/test']))

        assert observed is None
        mock_client.get_detail.assert_called_once_with('meta', ['10.1000/test'])
        mock_converter.convert_list.assert_called_once_with('meta', [])

    def test_bad_object_type(self):
        """A bad object type -> raise DataSourceError()."""

        ds = OpenCitationsDataSource(
            lambda: None,
            lambda: None,
        )

        with pytest.raises(DataSourceError):
            list(ds.get_by_id('bad_type', ['10.1000/test']))

    def test_supported_types(self):
        """OpenCitationsDataSource().supported_types."""

        ds = OpenCitationsDataSource(
            None,
            None,
        )

        observed = ds.supported_types

        assert observed == ['meta']
