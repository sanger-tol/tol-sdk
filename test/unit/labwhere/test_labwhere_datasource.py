# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

import pytest

from tol.core import DataSourceError
from tol.labwhere import LabwhereDataSource


class TestLabwhereDataSource:
    def test_get_by_id_found(self):
        """200 response, no token"""

        mock_client = Mock()

        mock_response = Mock()
        mock_client.get_detail.return_value = mock_response

        mock_data_object = Mock()

        mock_lc_converter = Mock()
        mock_lc_converter.convert.return_value = mock_data_object

        ds = LabwhereDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('location', ['an ID']))
        assert observed == mock_data_object

        mock_client.get_detail.assert_called_once_with(
            'location',
            'an ID'
        )
        mock_lc_converter.convert.assert_called_once_with(
            mock_response
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning `None`
        mock_client.get_detail.return_value = None

        mock_lc_converter = Mock()

        ds = LabwhereDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('location', ['an ID']))
        assert observed is None

        mock_client.get_detail.assert_called_once_with(
            'location',
            'an ID'
        )
        mock_lc_converter.convert.assert_not_called()

    def test_bad_object_type(self):
        """A bad object type -> raise `DataSourceError()`"""

        ds = LabwhereDataSource(
            lambda: None,
            lambda: None
        )

        with pytest.raises(DataSourceError):
            ds.get_by_id('test', ['does not matter at all'])

    def test_supported_types(self):
        """
        `LabwhereDataSource().supported_types` calls
        `config_attribute_types()` on client
        """
        expected = ['location', 'location_type']

        ds = LabwhereDataSource(
            None,
            None
        )

        observed = ds.supported_types

        assert observed == expected

    def test_get_to_one_relation_parent(self):
        """
        `ApiDataSource().get_to_one_relation()` calls
        `.get_recursive_relation()` internally with one hop.
        """

        mock_ds = create_autospec(LabwhereDataSource)

        mock_object = Mock()
        type(mock_object).type = 'location'
        type(mock_object).id = 'id'
        type(mock_object).parent = 'api/locations/other'

        # call OG method on class, with mock instance (self)
        LabwhereDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'parent_location'
        )

        mock_ds.get_one.assert_called_once_with(
            'location',
            'other'
        )

    def test_get_to_one_relation_location_type(self):
        """
        `ApiDataSource().get_to_one_relation()` calls
        `.get_recursive_relation()` internally with one hop.
        """

        mock_ds = create_autospec(LabwhereDataSource)

        mock_object = Mock()
        type(mock_object).type = 'location'
        type(mock_object).id = 'id'
        type(mock_object).location_type_id = 'lt-id'

        # call OG method on class, with mock instance (self)
        LabwhereDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'location_type'
        )

        mock_ds.get_one.assert_called_once_with(
            'location_type',
            'lt-id'
        )
