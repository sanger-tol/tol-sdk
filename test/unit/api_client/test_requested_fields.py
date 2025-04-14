# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

import pytest

from tol.api_client import ApiDataSource
from tol.api_client.client import JsonApiClient
from tol.api_client.converter import (
    DataObjectConverter,
    JsonApiConverter,
)
from tol.api_client.filter import ApiFilter
from tol.api_client.parser import DefaultParser
from tol.core import DataObject, core_data_object


@pytest.fixture
def requested_api_client() -> JsonApiClient:
    mock_client: JsonApiClient = create_autospec(
        JsonApiClient,
        spec_set=True
    )

    mock_client.config_attribute_types.return_value = {
        'a': {},
        'b': {},
        'c': {},
    }

    mock_client.config_relationships.return_value = {
        'a': {
            'one': {
                'b': 'b'
            }
        },
        'b': {
            'one': {
                'c': 'c'
            }
        },
    }

    mock_client.config_operations.return_value = {
        'a': {
            'noauth': [
                'detailGet',
                'listGet',
            ]
        }
    }

    return mock_client


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
    requested_do_converter: DataObjectConverter,
    requested_filter: ApiFilter,
) -> ApiDataSource:

    class _Manager:
        api_ds: ApiDataSource

        def get_json_converter(self) -> JsonApiConverter:
            parser = DefaultParser(
                {
                    'a': self.api_ds,
                    'b': self.api_ds,
                    'c': self.api_ds,
                }
            )
            return JsonApiConverter(parser)

    manager = _Manager()

    api_ds = ApiDataSource(
        lambda: requested_api_client,
        manager.get_json_converter,
        lambda: requested_do_converter,
        lambda: requested_filter,
    )
    core_data_object(api_ds)
    manager.api_ds = api_ds

    return api_ds


class TestRequestedFields:
    """
    `requested_fields` on `ApiDataSource`.
    """

    def test_get_one(
        self,
        requested_api_ds: ApiDataSource,
        requested_api_client: JsonApiClient,
    ):

        requested_api_client.get_detail.return_value = {
            'data': self.__get_mock_dump()
        }

        ret_a = requested_api_ds.get_one(
            'a',
            'A',
            requested_fields=['b.id', 'b.c.id']
        )

        self.__assert_no_further_fetches(
            ret_a,
            requested_api_client
        )

    def test_get_list(
        self,
        requested_api_ds: ApiDataSource,
        requested_api_client: JsonApiClient,
    ):

        requested_api_client.get_list_page.return_value = {
            'data': [
                self.__get_mock_dump(),
            ],
            'meta': {
                'count': 1
            }
        }

        (ret_a,) = list(
            requested_api_ds.get_list(
                'a',
                requested_fields=['b.id', 'b.c.id']
            )
        )

        self.__assert_no_further_fetches(
            ret_a,
            requested_api_client
        )

    def test_get_list_page(
        self,
        requested_api_ds: ApiDataSource,
        requested_api_client: JsonApiClient,
    ):

        requested_api_client.get_list_page.return_value = {
            'data': [
                self.__get_mock_dump(),
            ],
            'meta': {
                'count': 1
            }
        }

        (ret_a_iter, _) = requested_api_ds.get_list_page(
            'a',
            requested_fields=['b.id', 'b.c.id']
        )
        (ret_a,) = list(ret_a_iter)

        self.__assert_no_further_fetches(
            ret_a,
            requested_api_client
        )

    def __assert_no_further_fetches(
        self,
        ret_a: DataObject,
        requested_api_client: JsonApiClient
    ) -> None:

        ret_b = ret_a.b
        assert ret_b.id == 'B'
        requested_api_client.get_to_one_relation_recursive.assert_not_called()

        ret_c = ret_b.c
        assert ret_c.id == 'C'
        requested_api_client.get_to_one_relation_recursive.assert_not_called()

    def __get_mock_dump(self):
        return {
            'type': 'a',
            'id': 'A',
            'relationships': {
                'b': {
                    'data': {
                        'type': 'b',
                        'id': 'B',
                        'relationships': {
                            'c': {
                                'data': {
                                    'type': 'c',
                                    'id': 'C',
                                }
                            }
                        }
                    }
                }
            }
        }
