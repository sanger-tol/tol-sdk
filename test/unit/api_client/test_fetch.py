# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.api_client import ApiDataSource
from tol.api_client.client import JsonApiClient
from tol.api_client.converter import DataObjectConverter, JsonApiConverter
from tol.api_client.filter import ApiFilter
from tol.api_client.parser import DefaultParser, Parser
from tol.core import core_data_object


@pytest.fixture(scope='function')
def api_client() -> JsonApiClient:
    mock = create_autospec(
        JsonApiClient,
        spec_set=True
    )

    mock.config_attribute_types.return_value = {
        'root': {},
        'rel': {'str_column': 'str'}
    }
    mock.config_operations.return_value = {
        'root': {
            'noauth': ['detailGet', 'relational']
        },
        'rel': {
            'noauth': ['detailGet', 'relational']
        }
    }
    mock.config_relationships.return_value = {
        'root': {
            'one': {
                'relation': 'rel'
            }
        }
    }

    return mock


@pytest.fixture(scope='function')
def parser() -> Parser:
    return create_autospec(
        Parser,
        spec_set=True
    )


@pytest.fixture(scope='function')
def json_api_converter(
    parser: Parser
) -> JsonApiConverter:

    return JsonApiConverter(
        parser
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
    api_filter: ApiFilter,
    parser: Parser
) -> ApiDataSource:

    ds = ApiDataSource(
        lambda: api_client,
        lambda: json_api_converter,
        lambda: data_object_converter,
        lambda: api_filter
    )
    core_data_object(ds)

    # resolves a chicken-and-the-egg problem
    parser_override = DefaultParser(
        {
            'root': ds,
            'rel': ds
        }
    )
    parser.parse.side_effect = parser_override.parse

    return ds


class TestNoFetch:
    """No superfluous fetches"""

    def test_none(
        self,
        api_ds: ApiDataSource,
        api_client: JsonApiClient
    ):
        """
        A `to_one` relation is None ->
        no further fetches when accessing it.
        """

        api_client.get_detail.return_value = {
            'data': {
                'type': 'root',
                'id': '404',
                'relationships': {
                    'relation': None
                }
            }
        }

        obj = api_ds.get_one('root', '404')

        assert obj is not None
        api_client.get_detail.assert_called_once()
        api_client.get_to_one_relation_recursive.assert_not_called()

        assert obj.relation is None
        api_client.get_detail.assert_called_once()
        api_client.get_to_one_relation_recursive.assert_not_called()

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

        api_client.get_detail.return_value = {
            'data': {
                'type': 'root',
                'id': '400',
                'relationships': {
                    'relation': {
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
        }

        obj = api_ds.get_one('root', '400')

        assert obj is not None
        api_client.get_detail.assert_called_once()
        api_client.get_to_one_relation_recursive.assert_not_called()

        relation = obj.relation
        assert relation is not None

        assert relation.str_column == 'NO FETCH!'

        # no more fetches since last time
        api_client.get_detail.assert_called_once()
        api_client.get_to_one_relation_recursive.assert_not_called()
