# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import pytest

from tol.core import (
    DataObject,
    DataSourceError,
    DataSourceFilter,
)
from tol.ena import EnaDataSource


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


class TestEnaDataSource:
    def test_get_by_id_found(self):
        """200 response"""

        mock_client = Mock()

        mock_response = {
            'study_accession': 'PRJEB48587',
        }

        mock_client.get_detail.return_value = ([mock_response])

        mock_lc_converter = Mock()

        ds = EnaDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None
        )

        ds.data_object_factory = lambda: Mock()

        mock_data_object = _get_mock_data_object(
            type_='study',
            id_='an ID',
        )

        mock_lc_converter.convert_list.return_value = ([mock_data_object], 1)

        observed = list(ds.get_by_id('study', ['an ID']))
        assert observed == [mock_data_object]

        mock_client.get_detail.assert_called_once_with(
            'study',
            ['an ID'],
        )

        mock_lc_converter.convert_list.assert_called_once_with(
            'study',
            [mock_response]
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning 'None'
        mock_client.get_detail.return_value = []
        mock_response = {
            'study_accession': 'PRJEB48587',
        }
        mock_client.get_fields.return_value = mock_response

        mock_lc_converter = Mock()
        mock_lc_converter.convert_list.return_value = ([], 0)

        ds = EnaDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('study', ['an ID']))
        assert observed is None

        mock_client.get_detail.assert_called_once_with(
            'study',
            ['an ID'],
        )

        mock_lc_converter.convert_list.assert_called_once_with(
            'study',
            []
        )

    def test_bad_object_type(self):
        """A bad object type -> raise DataSourceError()"""
        mock_client = Mock()

        # mock a 404 returning 'None'
        mock_client.get_detail.return_value = []
        mock_response = {
            'study_accession': 'PRJEB48587',
        }
        mock_client.get_fields.return_value = mock_response

        ds = EnaDataSource(
            lambda: mock_client,
            lambda: None,
            None
        )
        with pytest.raises(DataSourceError):
            list(ds.get_by_id('test', ['does not matter at all']))

    def test_get_list_populated(self):
        """
        `EnaDataSource().get_listpage()` gets populated list
        from client. `filter` is populated.
        """

        mock_objs = [Mock() for _ in range(3)]

        mock_json = Mock()

        mock_client = Mock()
        mock_client.config.attribute_types.return_value = {
            'assembly': {},
        }
        mock_client.get_list_page.return_value = (mock_json)
        mock_response = {}
        mock_client.get_fields.return_value = mock_response
        mock_converter = Mock()
        mock_converter.convert_list.return_value = (mock_objs, 3)

        mock_filter = Mock()
        mock_filter.dumps.return_value = 'tax_id="9662"'

        ena_ds = EnaDataSource(
            lambda: mock_client,
            lambda: mock_converter,
            lambda: mock_filter
        )

        f = DataSourceFilter()
        f.and_ = {'tax_id': {'eq': {'value': '9662'}}}

        observed = list(ena_ds.get_list(
            'assembly',
            object_filters=f
        ))

        mock_client.get_list.assert_called_once_with(
            'assembly',
            filter_string='tax_id="9662"'
        )
        mock_filter.dumps.assert_called_once_with(f)
        assert observed == (list(mock_objs))

    def test_supported_types(self):
        expected = [
            'assembly', 'read_run', 'sample', 'study', 'taxon',
            'checklist', 'submittable_taxon'
        ]
        mock_client = Mock()
        mock_response = {}

        mock_client.get_fields.return_value = mock_response
        ds = EnaDataSource(
            lambda: mock_client,
            lambda: None,
            None
        )

        observed = ds.supported_types
        assert observed == expected
