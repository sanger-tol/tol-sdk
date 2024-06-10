# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.api_client2 import ApiDataSource
from tol.api_client2.client import JsonApiClient
from tol.api_client2.converter import DataObjectConverter, JsonApiConverter
from tol.api_client2.filter import ApiFilter
from tol.core import DataObject, DataSourceError
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

    return ApiDataSource(
        lambda: api_client,
        lambda: json_api_converter,
        lambda: data_object_converter,
        lambda: api_filter
    )


class TestNoFetch:
    """No superfluous fetches"""

    def test_get_recursive_relation(
        self,
        api_ds: ApiDataSource,
        api_client: JsonApiClient
    ):
        """
        Endpoint returns relations +
        getting relation.attr on root
        -> none of the following:

        - get_recursive_relation (on
          root type)
        - get_by_id (on relation type)
        - get_one (on relation type)
        """
