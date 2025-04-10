# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.api_client import ApiDataSource
from tol.api_client.client import JsonApiClient
from tol.api_client.converter import (
    DataObjectConverter,
    JsonApiConverter,
)
from tol.api_client.filter import ApiFilter
from tol.core import (
    DataObject,
    core_data_object,
)


@pytest.fixture
def requested_api_client() -> JsonApiClient:
    return create_autospec(
        JsonApiClient,
        spec_set=True
    )


@pytest.fixture
def requested_json_converter() -> JsonApiConverter:
    return create_autospec(
        JsonApiConverter,
        spec_set=True
    )


@pytest.fixture
def requested_do_converter() -> DataObjectConverter:
    return create_autospec(
        DataObjectConverter,
        spec_set=True
    )


@pytest.fixture
def requested_filter() -> ApiFilter:
    return create_autospec(
        ApiFilter,
        spec_set=True
    )


@pytest.fixture
def requested_api_ds(
    requested_api_client: JsonApiClient,
    requested_json_converter: JsonApiConverter,
    requested_do_converter: DataObjectConverter,
    requested_filter: ApiFilter,
) -> ApiDataSource:

    api_ds = ApiDataSource(
        lambda: requested_api_client,
        lambda: requested_json_converter,
        lambda: requested_do_converter,
        lambda: requested_filter,
    )
    core_data_object(api_ds)

    return api_ds


class TestRequestedFields:
    """
    `requested_fields` on `ApiDataSource`.
    """

    def test_get_one(
        self,
        requested_api_ds: ApiDataSource,
        requested_api_client: JsonApiClient,
        requested_json_converter: JsonApiConverter,
    ):

        pass

    def test_get_list(self):
        pass

    def test_get_list_page(self):
        pass
