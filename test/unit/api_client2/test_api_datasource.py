# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional
from unittest.mock import Mock, call

import pytest

from tol.api_client2 import ApiDataSource
from tol.core import DataSourceError


class TestApiDataSource:
    def test_get_by_id_found(self):
        """200 response, no token"""

        mock_client = Mock()

        mock_response = Mock()
        mock_client.get_detail.return_value = mock_response
        mock_client.config_operations.return_value = {
            'test': {'auth': ['detailGet']}
        }
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }

        mock_data_object = Mock()

        mock_jc_converter = Mock()
        mock_jc_converter.convert.return_value = mock_data_object

        ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc_converter,
            None,
            None
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('test', ['an ID']))
        assert observed == mock_data_object

        mock_client.get_detail.assert_called_once_with(
            'test',
            'an ID'
        )
        mock_jc_converter.convert.assert_called_once_with(
            mock_response
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning `None`
        mock_client.get_detail.return_value = None
        # pre fligt checks
        mock_client.config_operations.return_value = {
            'test': {'auth': ['detailGet']}
        }
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }

        mock_jc_converter = Mock()

        ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc_converter,
            None,
            None
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('test', ['an ID']))
        assert observed is None

        mock_client.get_detail.assert_called_once_with(
            'test',
            'an ID'
        )
        mock_jc_converter.convert.assert_not_called()

    def test_bad_object_type(self):
        """A bad object type -> raise `DataSourceError()`"""

        mock_client = Mock()
        mock_client.config_attribute_types.return_value = {}
        mock_client.config_operations.return_value = {
            'test': {'auth': ['detailGet']}
        }

        ds = ApiDataSource(
            lambda: mock_client,
            lambda: None,
            None,
            None
        )

        with pytest.raises(DataSourceError):
            ds.get_by_id('test', ['does not matter at all'])

    def test_supported_types(self):
        """
        `ApiDataSource().supported_types` calls
        `config_attribute_types()` on client
        """

        in_ = {
            'a': {
                '1': 'str'
            },
            'b': {
                '2': 'bool',
                '4': 'int'
            }
        }
        expected = ['a', 'b']

        mock_client = Mock()
        mock_client.config_attribute_types.return_value = in_

        ds = ApiDataSource(
            lambda: mock_client,
            None,
            None,
            None
        )

        observed = ds.supported_types

        assert observed == expected

    def test_get_list_page_empty(self):
        """
        `ApiDataSource().get_list_page()` gets empty list
        from client. `filter` and `sort_by` are not `None`,
        and fully populated.
        """

        expected = ([], 84959859)

        mock_json = Mock()

        mock_client = Mock()
        mock_client.config_operations.return_value = {
            'test': {'auth': ['listGet']}
        }
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }
        mock_client.get_list_page.return_value = mock_json

        mock_json_converter = Mock()
        mock_json_converter.convert_list.return_value = expected

        mock_ds_filter = Mock()

        mock_api_filter = Mock()
        mock_api_filter.dumps.return_value = 'I am a filter!!!'

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_json_converter,
            None,
            lambda: mock_api_filter
        )

        observed = api_ds.get_list_page(
            'test',
            3489,
            page_size=8989,
            object_filters=mock_ds_filter,
            sort_by='ludicrous_speed-'
        )

        mock_client.get_list_page.assert_called_once_with(
            'test',
            3489,
            8989,
            filter_string='I am a filter!!!',
            sort_string='ludicrous_speed-'
        )
        mock_api_filter.dumps.assert_called_once_with(
            mock_ds_filter
        )
        mock_json_converter.convert_list.assert_called_once_with(
            mock_json
        )

        assert observed == expected

    def test_get_list_page_populated(self):
        """
        `ApiDataSource().get_list_page()` gets populated list
        from client. `filter` and `sort_by` are `None`
        """

        mock_objs = [Mock() for _ in range(3)]
        expected = (mock_objs, 200)

        mock_json = Mock()

        mock_client = Mock()
        mock_client.config_operations.return_value = {
            'test': {'auth': ['listGet']}
        }
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }
        mock_client.get_list_page.return_value = mock_json

        mock_json_converter = Mock()
        mock_json_converter.convert_list.return_value = expected

        mock_api_filter = Mock()

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_json_converter,
            None,
            lambda: mock_api_filter
        )

        observed = api_ds.get_list_page(
            'test',
            101,
            page_size=3,
        )

        mock_client.get_list_page.assert_called_once_with(
            'test',
            101,
            3,
            filter_string=None,
            sort_string=None
        )
        mock_api_filter.dumps.assert_not_called()
        mock_json_converter.convert_list.assert_called_once_with(
            mock_json
        )

        assert observed == expected

    def test_supported_operations(self):
        """`ApiDataSource().supported_operations`"""

        in_ = {
            'thing1': {
                'noauth': ['aggregate', 'delete']
            },
            'thing2': {
                'auth': ['detailGet'],
                'noauth': ['listGet', 'upsert']
            }
        }

        expected = {
            'thing1': ['aggregate', 'delete'],
            'thing2': ['detailGet', 'listGet', 'upsert']
        }

        mock_client = Mock()
        mock_client.config_operations.return_value = in_

        api_ds = ApiDataSource(
            lambda: mock_client,
            None,
            None,
            None
        )

        observed = api_ds.supported_operations
        assert observed == expected

    def test_unsupported_operation(self):
        """Calling an unsupported method for an `object_type`"""
        in_ = {
            'thing1': {
                'noauth': ['aggregate', 'delete']
            },
            'thing2': {
                'auth': ['detailGet'],
                'noauth': ['listGet', 'upsert']
            }
        }

        mock_client = Mock()
        mock_client.config_operations.return_value = in_
        mock_client.config_attribute_types.return_value = {
            'thing1': {},
            'thing2': {}
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            Mock(),
            None,
            None
        )

        with pytest.raises(DataSourceError):
            api_ds.get_by_id('thing1', ['unsupported operation lol'])

    def test_upsert(self):
        """`ApiDataSource().upsert()`"""

        mock_objects = [Mock() for _ in range(3)]

        mock_do_converter = Mock()
        mock_do_converter.convert_list.side_effect = (
            lambda o: o
        )

        mock_client = Mock()
        mock_client.config_operations.return_value = {
            'test': {'auth': ['upsert']}
        }
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            None,
            lambda: mock_do_converter,
            None
        )

        api_ds.upsert('test', mock_objects)

        mock_do_converter.convert_list.assert_called_once_with(
            mock_objects
        )
        assert mock_client.upsert.call_args_list == [
            call('test', mock_objects)
        ]

    def test_get_list(self):
        """
        `ApiDataSource().get_list()` stops generating results
        upon reaching an empty page.
        """

        mock_objs = [Mock() for _ in range(3)]
        expected = mock_objs

        convert_calls = [call([m]) for m in mock_objs] + [call([])]

        def __get_lp(
            object_type: str,
            page: int,
            page_size: int,
            filter_string: Optional[str] = None,
            sort_string: Optional[str] = None
        ) -> list[Mock]:

            return [mock_objs[page - 1]] if page <= 3 else []

        client_calls = [
            call(
                'test_hype',
                i,
                1,
                filter_string='akdfuom'
            )
            for i in range(1, 5)
        ]

        mock_client = Mock()
        mock_client.config_operations.return_value = {
            'test_hype': {'auth': ['listGet']}
        }
        mock_client.config_attribute_types.return_value = {
            'test_hype': {}
        }
        mock_client.get_list_page.side_effect = __get_lp

        mock_json_converter = Mock()
        mock_json_converter.convert_list.side_effect = lambda l: (l, None)

        mock_api_filter = Mock()
        mock_api_filter.dumps.return_value = 'akdfuom'

        mock_ds_filter = Mock()

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_json_converter,
            None,
            lambda: mock_api_filter
        )
        api_ds.page_size = 1

        observed = list(
            api_ds.get_list('test_hype', mock_ds_filter)
        )

        assert mock_client.get_list_page.call_args_list == client_calls
        mock_api_filter.dumps.assert_called_once_with(mock_ds_filter)
        assert mock_json_converter.convert_list.call_args_list == convert_calls

        assert observed == expected
