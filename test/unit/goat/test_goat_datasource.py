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
from tol.goat import ElasticDataSource


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


class TestGoatDataSource:
    def test_get_by_id_found(self):
        """200 response, no token"""

        mock_client = Mock()

        mock_response = {'result': {'taxon_id': 'an ID'}}
        mock_client.get_detail.return_value = ([mock_response], 1)

        mock_lc_converter = Mock()

        ds = ElasticDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None
        )
        ds.data_object_factory = lambda: Mock()

        mock_data_object = _get_mock_data_object(
            type_='taxon',
            id_='an ID'
        )
        mock_lc_converter.convert_list.return_value = ([mock_data_object], 1)

        observed = list(ds.get_by_id('taxon', ['an ID']))
        assert observed == [mock_data_object]

        mock_client.get_detail.assert_called_once_with(
            'taxon',
            ['an ID']
        )
        mock_lc_converter.convert_list.assert_called_once_with(
            [mock_response]
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning `None`
        mock_client.get_detail.return_value = ([], 0)

        mock_lc_converter = Mock()
        mock_lc_converter.convert_list.return_value = ([], 0)

        ds = ElasticDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None
        )
        ds.data_object_factory = lambda: Mock()

        observed = list(ds.get_by_id('taxon', ['an ID']))
        assert observed == [None]

        mock_client.get_detail.assert_called_once_with(
            'taxon',
            ['an ID']
        )
        mock_lc_converter.convert_list.assert_called_once_with(
            []
        )

    def test_bad_object_type(self):
        """A bad object type -> raise `DataSourceError()`"""

        ds = ElasticDataSource(
            lambda: None,
            lambda: None,
            None
        )
        with pytest.raises(DataSourceError):
            list(ds.get_by_id('test', ['does not matter at all']))

    def test_supported_types(self):
        """
        `GoatDataSource().supported_types` calls
        `config_attribute_types()` on client
        """
        expected = ['taxon']

        ds = ElasticDataSource(
            None,
            None,
            None
        )

        observed = ds.supported_types

        assert observed == expected
