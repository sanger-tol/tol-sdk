# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

import pytest

from tol.copo import CopoDataSource
from tol.core import DataSourceError


class TestCopoDataSource:
    def test_get_by_id_found(self):
        """200 response, no token"""

        mock_client = Mock()

        mock_response = [{}]
        mock_client.get_detail.return_value = mock_response

        mock_data_object = Mock()

        mock_lc_converter = Mock()
        mock_lc_converter.convert.return_value = mock_data_object

        ds = CopoDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('manifest', ['an ID']))
        assert observed == mock_data_object

        mock_client.get_detail.assert_called_once_with(
            'manifest',
            ['an ID']
        )
        mock_lc_converter.convert.assert_called_once_with(
            {}
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning `None`
        mock_client.get_detail.return_value = [None]

        mock_lc_converter = Mock()

        ds = CopoDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('manifest', ['an ID']))
        assert observed is None

        mock_client.get_detail.assert_called_once_with(
            'manifest',
            ['an ID']
        )
        mock_lc_converter.convert.assert_not_called()

    def test_bad_object_type(self):
        """A bad object type -> raise `DataSourceError()`"""

        ds = CopoDataSource(
            lambda: None,
            lambda: None
        )

        with pytest.raises(DataSourceError):
            ds.get_by_id('test', ['does not matter at all'])

    def test_supported_types(self):
        """
        `CopoDataSource().supported_types` calls
        `config_attribute_types()` on client
        """
        expected = ['manifest', 'sample']

        ds = CopoDataSource(
            None,
            None
        )

        observed = ds.supported_types

        assert observed == expected

    def test_get_to_one_relation_manifest(self):
        """
        `CopoDataSource().get_to_one_relation()` calls
        `.get_recursive_relation()` internally with one hop.
        """

        mock_ds = create_autospec(CopoDataSource)

        mock_object = Mock()
        type(mock_object).type = 'sample'
        type(mock_object).id = 'id'
        type(mock_object).manifest_id = 'manifest-id'

        # call OG method on class, with mock instance (self)
        CopoDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'manifest'
        )

        mock_ds.get_one.assert_called_once_with(
            'manifest',
            'manifest-id'
        )
