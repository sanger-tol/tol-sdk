# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.api_client import ApiDataSource
from tol.api_client.client import JsonApiClient
from tol.api_client.converter import (
    DataObjectConverter,
    JsonApiConverter
)
from tol.api_client.filter import ApiFilter
from tol.api_client.parser import DefaultParser
from tol.core import core_data_object


@pytest.fixture
def client() -> JsonApiClient:
    mock_client: JsonApiClient = create_autospec(
        JsonApiClient,
        spec_set=True
    )

    mock_client.config_attribute_types.return_value = {
        'test': {}
    }

    return mock_client


@pytest.fixture
def json_api_converter() -> JsonApiConverter:
    return create_autospec(
        JsonApiConverter,
        spec_set=True
    )


@pytest.fixture
def data_object_converter() -> DataObjectConverter:
    return create_autospec(
        DataObjectConverter,
        spec_set=True
    )


@pytest.fixture
def api_filter() -> ApiFilter:
    return create_autospec(
        ApiFilter,
        spec_set=True
    )


@pytest.fixture
def api_ds(
    client: JsonApiClient,
    json_api_converter: JsonApiConverter,
    data_object_converter: DataObjectConverter,
    api_filter: ApiFilter
) -> ApiDataSource:

    api_ds = ApiDataSource(
        lambda: client,
        lambda: json_api_converter,
        lambda: data_object_converter,
        lambda: api_filter
    )
    core_data_object(api_ds)

    api_ds.page_size = 3

    # prevent a chicken-and-the-egg problem
    concrete_json_converter = JsonApiConverter(
        DefaultParser(
            {
                'test': api_ds
            }
        )
    )
    json_api_converter.convert_cursor_page.side_effect = (
        concrete_json_converter.convert_cursor_page
    )
    json_api_converter.convert_list.side_effect = (
        concrete_json_converter.convert_list
    )

    return api_ds


class TestGetList:
    """
    `ApiDataSource.get_list()` uses `.get_cursor_page()`
    if and only if `cursor` is in `.supported_operations`.
    """

    def test_cursor(
        self,
        api_ds: ApiDataSource,
        client: JsonApiClient
    ):
        """Should use cursor pagination"""

        client.config_operations.return_value = {
            'test': {
                'noauth': ['cursor']
            }
        }
        client.get_cursor_page.return_value = {
            'meta': {
                'search_after': ['excellent']
            },
            'data': [
                {
                    'type': 'test',
                    'id': 'excellent'
                }
            ]
        }

        results = list(
            api_ds.get_list('test')
        )

        assert len(results) == 1
        obj = results[0]
        assert obj.type == 'test'
        assert obj.id == 'excellent'

        client.get_cursor_page.assert_called_once()
        client.get_list_page.assert_not_called()

    def test_regular_pagination(
        self,
        api_ds: ApiDataSource,
        client: JsonApiClient
    ):
        """Should use regular pagination, not cursor"""

        client.config_operations.return_value = {
            'test': {
                'noauth': ['listGet']
            }
        }
        client.get_list_page.return_value = {
            'data': [
                {
                    'type': 'test',
                    'id': 'excellent'
                }
            ]
        }

        results = list(
            api_ds.get_list('test')
        )

        assert len(results) == 1
        obj = results[0]
        assert obj.type == 'test'
        assert obj.id == 'excellent'

        client.get_list_page.assert_called_once()
        client.get_cursor_page.assert_not_called()
