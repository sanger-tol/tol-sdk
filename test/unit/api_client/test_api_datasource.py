# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional
from unittest.mock import Mock, PropertyMock, call, create_autospec

import pytest

from tol.api_client import ApiDataSource
from tol.api_client.client import JsonApiClient
from tol.api_client.converter import JsonApiConverter
from tol.core import DataObject, DataSourceError
from tol.core.operator import ReturnMode
from tol.core.relationship import RelationshipConfig


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
            sort_string='ludicrous_speed-',
            requested_fields=None,
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
            sort_string=None,
            requested_fields=None,
        )
        mock_api_filter.dumps.assert_not_called()
        mock_json_converter.convert_list.assert_called_once_with(
            mock_json
        )

        assert observed == expected

    def test_get_stats(self):
        """
        `ApiDataSource().get_list_pageget_stats()` gets stats
        from client. `filter` is `None`
        """

        mock_stats = {
            'stats': {
                'field1_min': 10,
                'field1_max': 20,
                'field1_unique': 4,
                'field2_min': 'aaa',
                'field2_max': 'zzz',
                'field2_unique': 7
            }
        }
        expected = mock_stats

        mock_json = Mock()

        mock_client = Mock()
        mock_client.config_operations.return_value = {
            'test': {'auth': ['stats']}
        }
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }
        mock_client.get_stats.return_value = mock_json

        mock_json_converter = Mock()
        mock_json_converter.convert_stats.return_value = expected

        mock_api_filter = Mock()

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_json_converter,
            None,
            lambda: mock_api_filter
        )

        observed = api_ds.get_stats(
            'test',
            stats=['min', 'max', 'unique'],
            stats_fields=['field1', 'field2']
        )

        mock_client.get_stats.assert_called_once_with(
            'test',
            stats_string='min,max,unique',
            stats_fields_string='field1,field2',
            filter_string=None
        )
        mock_api_filter.dumps.assert_not_called()
        mock_json_converter.convert_stats.assert_called_once_with(
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

        mock_jc_converter = Mock()
        mock_jc_converter.convert_list.return_value = [None, None]

        mock_client = Mock()
        mock_client.config_operations.return_value = {
            'test': {'auth': ['upsert']}
        }
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }
        mock_client.config_return_mode.return_value = {
            'test': ReturnMode.NONE
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc_converter,
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
        mock_json_converter.convert_list.side_effect = lambda o: (o, None)

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

    def test_get_recursive_relation(self):
        """`ApiDataSource().get_recursive_relation()`"""

        expected = Mock()

        source = Mock()
        type(source).type = PropertyMock(return_value='a')
        type(source).id = PropertyMock(return_value='id_MINE')

        mock_client = create_autospec(JsonApiClient)
        mock_client.config_attribute_types.return_value = {
            c: {} for c in 'abcd'
        }
        mock_client.config_operations.return_value = {
            c: {'noauth': ['relational']}
            for c in 'abcd'
        }
        mock_client.get_to_one_relation_recursive.return_value = (
            expected
        )

        mock_jc = create_autospec(JsonApiConverter)
        mock_jc.convert.return_value = expected
        mock_jc.convert_relationship_config.return_value = {
            c: RelationshipConfig(
                to_one={f'test_{c.upper()}': 'abcd'[i + 1]}
            )
            for i, c in enumerate('abcd')
            if c != 'd'
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc,
            None,
            None
        )

        observed = api_ds.get_recursive_relation(
            source,
            ['test_A', 'test_B']
        )

        mock_client.get_to_one_relation_recursive.assert_called_once_with(
            'a',
            'id_MINE',
            ['test_A', 'test_B']
        )
        mock_jc.convert.assert_called_once_with(expected)
        assert observed == expected

    def test_get_to_one_relation(self):
        """
        `ApiDataSource().get_to_one_relation()` calls
        `.get_recursive_relation()` internally with one hop.
        """

        mock_ds = create_autospec(ApiDataSource)
        type(mock_ds).supported_types = ['a']
        type(mock_ds).supported_operations = {
            'a': ['relational']
        }
        type(mock_ds).relationship_config = {
            'a': RelationshipConfig(to_one={'test_relation': 'y'})
        }

        mock_object = Mock()
        type(mock_object).type = 'a'
        type(mock_object).id = 'id'

        # call OG method on class, with mock instance (self)
        ApiDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'test_relation'
        )

        mock_ds.get_recursive_relation.assert_called_once_with(
            mock_object,
            ['test_relation']
        )

    def test_relationship_config(self):
        """
        `ApiDataSource().relationship_config` gets config from client
        and converts it using its `JsonApiConverter` factory
        """

        mock_config = Mock()

        expected = Mock()

        mock_client = create_autospec(JsonApiClient)
        mock_client.config_relationships.return_value = mock_config

        mock_jc = create_autospec(JsonApiConverter)
        mock_jc.convert_relationship_config.return_value = expected

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc,
            None,
            None
        )

        observed = api_ds.relationship_config

        mock_client.config_relationships.assert_called_once_with()
        mock_jc.convert_relationship_config.assert_called_once_with(
            mock_config
        )
        assert observed == expected

    def test_get_to_many_relations(self):
        """
        `ApiDataSource().get_to_many_relations()` generates from
        repeated calls to `.get_to_many_relations_page(), and stops
        on the first empty page.`
        """

        mock_ds = create_autospec(ApiDataSource)

        expected = [Mock() for _ in range(4)]

        def __many_page(
            source: DataObject,
            relationship_name: str,
            page: int,
            page_size: int
        ) -> list[DataObject]:

            return (
                [expected[page - 1]] if page <= 4
                else []
            ), None

        type(mock_ds).supported_types = ['a']
        type(mock_ds).supported_operations = {
            'a': ['relational']
        }
        type(mock_ds).relationship_config = {
            'a': RelationshipConfig(to_many={'plentiful': 'y'})
        }
        mock_ds.get_page_size.return_value = 1
        mock_ds.get_to_many_relations_page.side_effect = __many_page

        mock_object = Mock()
        type(mock_object).type = 'a'
        type(mock_object).id = 'id'

        # one more call than pages, as the last is empty
        expected_calls = [
            call(mock_object, 'plentiful', i, 1)
            for i in range(1, 6)
        ]

        # call OG method on class, with mock instance (self)
        observed = list(
            ApiDataSource.get_to_many_relations(
                mock_ds,
                mock_object,
                'plentiful'
            )
        )

        assert mock_ds.get_to_many_relations_page.call_args_list == (
            expected_calls
        )
        assert observed == expected

    def test_get_to_many_relations_page(self):
        """
        `ApiDataSource().get_to_many_relations_page()` uses the
        factories for `JsonApiClient` and `JsonApiConverter` as
        expected.
        """

        expected = [Mock() for _ in range(3)]

        mock_obj = Mock()
        type(mock_obj).type = PropertyMock(return_value='hype')
        type(mock_obj).id = PropertyMock(
            return_value='neverending_hype'
        )

        mock_client = create_autospec(JsonApiClient)
        mock_client.get_to_many_relations_page.return_value = expected
        mock_client.config_attribute_types.return_value = {
            'hype': {}
        }
        mock_client.config_operations.return_value = {
            'hype': {'auth': ['relational']}
        }

        mock_jc = create_autospec(JsonApiConverter)
        mock_jc.convert_list.return_value = expected
        mock_jc.convert_relationship_config.return_value = {
            'hype': RelationshipConfig(
                to_one={'does_it_end': 'nope'}
            )
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc,
            None,
            None
        )

        observed = list(
            api_ds.get_to_many_relations_page(
                mock_obj,
                'does_it_end',
                3940584,
                2394
            )
        )

        mock_client.get_to_many_relations_page.assert_called_once_with(
            'hype',
            'neverending_hype',
            'does_it_end',
            3940584,
            2394
        )
        mock_jc.convert_list.assert_called_once_with(expected)
        assert observed == expected

    def test_relational_methods_without_id(self):
        """
        All relational methods refuse a source `DataObject` instance
        with a `None` value for `.id`
        """

        mock_obj = Mock()
        type(mock_obj).type = PropertyMock(return_value='hype')
        # crucially - the id is `None`!
        type(mock_obj).id = PropertyMock(return_value=None)

        mock_client = create_autospec(JsonApiClient)
        mock_client.config_attribute_types.return_value = {
            'hype': {}
        }
        mock_client.config_operations.return_value = {
            'hype': {'auth': ['relational']}
        }

        mock_jc = create_autospec(JsonApiConverter)
        mock_jc.convert_relationship_config.return_value = {
            'hype': RelationshipConfig(
                to_one={'does_it_end': 'nope'},
                to_many={'it_does_not_end': 'yes'}
            )
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc,
            None,
            None
        )

        with pytest.raises(DataSourceError):
            api_ds.get_to_one_relation(mock_obj, 'does_it_end')
        with pytest.raises(DataSourceError):
            api_ds.get_recursive_relation(mock_obj, ['does_it_end'])
        with pytest.raises(DataSourceError):
            api_ds.get_to_many_relations(mock_obj, 'it_does_not_end')
        with pytest.raises(DataSourceError):
            api_ds.get_to_many_relations_page(
                mock_obj,
                'it_does_not_end',
                390483094,
                4059
            )

    def test_get_recursive_relation_none(self):
        """
        `ApiDataSource().get_recursive_relation()` is given `None`
        by its client -> returns `None` and doesn't convert
        """

        mock_obj = Mock()
        type(mock_obj).type = PropertyMock(return_value='a')
        type(mock_obj).id = PropertyMock(return_value='id')

        mock_client = create_autospec(JsonApiClient)
        mock_client.get_to_one_relation_recursive.return_value = None
        mock_client.config_attribute_types.return_value = {
            'a': {}
        }
        mock_client.config_operations.return_value = {
            'a': {'noauth': ['relational']}
        }

        mock_jc = create_autospec(JsonApiConverter)
        mock_jc.convert_relationship_config.return_value = {
            'a': RelationshipConfig(
                to_one={'does_it_end': 'nope'}
            )
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc,
            None,
            None
        )

        observed = api_ds.get_recursive_relation(
            mock_obj,
            ['does_it_end']
        )

        mock_jc.convert.assert_not_called()
        assert observed is None

    def test_get_to_one_relation_none(self):
        """
        `ApiDataSource().get_to_one_relation()` is given `None` by its
        client -> returns `None` and doesn't convert
        """

        mock_obj = Mock()
        type(mock_obj).type = PropertyMock(return_value='a')
        type(mock_obj).id = PropertyMock(return_value='id')

        mock_client = create_autospec(JsonApiClient)
        mock_client.get_to_one_relation_recursive.return_value = None
        mock_client.config_attribute_types.return_value = {
            'a': {}
        }
        mock_client.config_operations.return_value = {
            'a': {'noauth': ['relational']}
        }

        mock_jc = create_autospec(JsonApiConverter)
        mock_jc.convert_relationship_config.return_value = {
            'a': RelationshipConfig(
                to_one={'does_it_end': 'nope'}
            )
        }

        api_ds = ApiDataSource(
            lambda: mock_client,
            lambda: mock_jc,
            None,
            None
        )

        observed = api_ds.get_to_one_relation(mock_obj, 'does_it_end')

        mock_jc.convert.assert_not_called()
        assert observed is None
