# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import create_autospec

import pytest

from tol.api_client2 import ApiDataSource
from tol.api_client2.client import JsonApiClient
from tol.api_client2.converter import DataObjectConverter, JsonApiConverter
from tol.api_client2.filter import ApiFilter
from tol.core import DataObject, core_data_object
from tol.core.relationship import RelationshipConfig


@pytest.fixture(scope='function')
def api_client() -> JsonApiClient:
    return create_autospec(
        JsonApiClient,
        spec_set=True
    )


@pytest.fixture(scope='function')
def json_api_converter() -> JsonApiConverter:
    return create_autospec(
        JsonApiConverter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def data_object_converter() -> DataObjectConverter:
    return create_autospec(
        DataObjectConverter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def api_filter() -> ApiFilter:
    return create_autospec(
        ApiFilter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def api_ds(
    api_client: JsonApiClient,
    json_api_converter: JsonApiConverter,
    data_object_converter: DataObjectConverter,
    api_filter: ApiFilter
) -> ApiDataSource:

    ds = ApiDataSource(
        lambda: api_client,
        lambda: json_api_converter,
        lambda: data_object_converter,
        lambda: api_filter
    )
    core_data_object(ds)

    return ds


class TestNoFetch:
    """No superfluous fetches"""

    def test_get_by_id(
        self,
        api_ds: ApiDataSource,
        api_client: JsonApiClient
    ):
        """
        Endpoint returns relations +
        getting relation.attr on root
        -> none of the following are called
        on the client:

        - `get_detail`
        - `get_to_one_relation_recursive`
        """

        api_client.config_relationships.return_value = {
            'root': RelationshipConfig(
                to_one={
                    'relation': 'rel'
                }
            )
        }
        api_client.config_attribute_types.return_value = {
            'root': {},
            'rel': {'str_column': 'str'}
        }
        api_client.config_operations.return_value = {
            'root': {
                'noauth': ['detailGet', 'relational']
            },
            'rel': {
                'noauth': ['detailGet', 'relational']
            }
        }
        api_client.get_detail.return_value = {
            'data': {
                'type': 'root',
                'id': '400',
                'relationships': {
                    'data': {
                        'type': 'rel',
                        'id': '408',
                        'attributes': {
                            'str_column': 'NO FETCH!'
                        }
                    }
                }
            }
        }

        api_ds.get_one('root', '400')
