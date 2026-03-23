# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable
from unittest.mock import MagicMock, Mock, PropertyMock, create_autospec

import pytest

from tol.api_base.controller import Controller
from tol.api_base.misc import LegacyAggregationBody, LegacyAggregationParameters, ListGetParameters
from tol.api_client.exception import (
    ObjectNotFoundByIdException,
    RecursiveRelationNotFoundException,
    UninheritedOperationError,
    UnsupportedOperationError,
)
from tol.api_client.view import DefaultView, View
from tol.core import DataSource, DataSourceFilter, ReqFieldsTree, core_data_object
from tol.core.data_object import DataObject
from tol.core.operator import DetailGetter, LegacyAggregator, PageGetter, Relational


class _TestDataSource1(DataSource, DetailGetter):

    def get_by_id(self, object_type: str, object_ids: Iterable[str], *args, **kwargs):
        return [
            self.data_object_factory(object_type, {'id': object_id}) for object_id in object_ids
        ]

    @property
    def supported_types(self):
        return ['test2', 'test1']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _TestDataSource2(DataSource, PageGetter):
    def get_list_page(self, object_type: str, *args, **kwargs):
        return [self.data_object_factory(object_type, id_=str(i)) for i in range(20)], 20

    @property
    def supported_types(self):
        return ['test_A', 'test_B']

    @property
    def attribute_types(self) -> Dict:
        return {'test_A': {}, 'test_B': {}}


class _TestDataSource3(DataSource, LegacyAggregator, PageGetter):
    """Accounts for page number and size in results"""

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
        **kwargs,
    ):
        return [
            self.data_object_factory(
                object_type,
                id_=str(i + 1 + page_size * page_number),
                attributes={
                    'page': page_number,
                    'page_size': page_size,
                    'filter': object_filters.exact['column1'],
                    'sort_by': sort_by,
                },
            )
            for i in range(page_size)
        ], 560  # a very arbitrary number

    def get_aggregations(
        self, object_type: str, aggregations: Dict, object_filters: DataSourceFilter = None
    ) -> Dict:
        return {
            'completed_over_time': {
                'buckets': [
                    {
                        'key_as_string': '2015-04-01T00:00:00.000Z',
                        'key': 1427846400000,
                        'doc_count': 3,
                    },
                    {
                        'key_as_string': '2015-05-01T00:00:00.000Z',
                        'key': 1430438400000,
                        'doc_count': 0,
                    },
                ]
            }
        }

    @property
    def supported_types(self):
        return ['test_X']

    @property
    def attribute_types(self):
        return {'test_X': {}}


ds_1 = _TestDataSource1({})
ds_2 = _TestDataSource2({})
ds_3 = _TestDataSource3({})


CoreDataObject = core_data_object(ds_1, ds_2, ds_3)


class TestController:
    def test_good_object_type(self):
        expected = {
            'meta': {'total': 20, 'types': {}},
            'data': [{'type': 'test_B', 'id': str(i)} for i in range(20)],
        }
        controller = Controller(ds_2, DefaultView(ReqFieldsTree('test_B', ds_2)))
        observed = controller.get_list('test_B', ListGetParameters({}))
        rft = ReqFieldsTree('test_B', ds_2)
        controller = Controller(ds_2, DefaultView(rft), rft)
        observed = controller.get_list('test_B', ListGetParameters({}))
        assert observed == expected

    def test_not_found(self):
        """DataSource().get_by_id() returning [None] (no elements) causes 404 error"""

        class _TestDataSourceNotFound(_TestDataSource1):
            def get_by_id(self, *args, **kwargs):
                return [None]

        not_found_ds = _TestDataSourceNotFound({})
        rft = ReqFieldsTree('test2', not_found_ds)
        controller = Controller(not_found_ds, DefaultView(rft), rft)

        with pytest.raises(ObjectNotFoundByIdException):
            controller.get_detail('test2', 'anything goes too')

    def test_page_size_and_number(self):
        """Check that page_size and page_number are passed in correctly"""

        rft = ReqFieldsTree('test_X', ds_3)
        controller = Controller(ds_3, DefaultView(rft), rft)
        parsed = ListGetParameters(
            {
                'page': '90',
                'page_size': '10',
                'filter': """
                {"exact": {"column1": "value1"}}
            """,
                'sort_by': '-column1',
            }
        )
        expected = {
            'meta': {'total': 560, 'types': {}},
            'data': [
                {
                    'type': 'test_X',
                    'id': str(901 + i),
                    'attributes': {
                        'page': 90,
                        'page_size': 10,
                        'filter': 'value1',
                        'sort_by': '-column1',
                    },
                }
                for i in range(10)
            ],
        }
        observed = controller.get_list('test_X', parsed)
        assert expected == observed

    def test_aggregations(self):
        """Check that aggregations are working"""

        rft = ReqFieldsTree('test_X', ds_3)
        controller = Controller(ds_3, DefaultView(rft), rft)
        parsed = LegacyAggregationParameters(
            {
                'filter': """
                {"exact": {"column1": "value1"}}
            """
            }
        )
        body = LegacyAggregationBody(
            {
                'aggs': {
                    'completed_over_time': {
                        'date_histogram': {'field': 'complete_date', 'calendar_interval': 'month'}
                    }
                }
            }
        )
        expected = {
            'meta': {
                'aggregations': {
                    'completed_over_time': {
                        'buckets': [
                            {
                                'key_as_string': '2015-04-01T00:00:00.000Z',
                                'key': 1427846400000,
                                'doc_count': 3,
                            },
                            {
                                'key_as_string': '2015-05-01T00:00:00.000Z',
                                'key': 1430438400000,
                                'doc_count': 0,
                            },
                        ]
                    }
                },
                'types': {},
            },
            'data': [],
        }
        observed = controller.post_aggregations_legacy('test_X', parsed, body)
        assert expected == observed

    def test_unsupported_operation(self):
        """
        a DataSource that doesn't support the given operation raises
        an Exception
        """

        class _BadDataSource(DataSource):
            """Doesn't support anything"""

            def __init__(self) -> None:
                pass

            @property
            def attribute_types(self):
                raise NotImplementedError()

            @property
            def supported_types(self) -> list[str]:
                return ['no']

        bad_ds = _BadDataSource()
        rft = ReqFieldsTree('test', bad_ds)
        controller = Controller(bad_ds, DefaultView(rft), rft)
        query_args = ListGetParameters({'page': '1', 'page_size': '10'})
        with pytest.raises(UnsupportedOperationError):
            controller.get_detail('test', 'hype')
        with pytest.raises(UnsupportedOperationError):
            controller.get_list('test', query_args=query_args)
        with pytest.raises(UnsupportedOperationError):
            controller.post_aggregations_legacy('test', MagicMock(), MagicMock(), MagicMock())

    def test_operation_implemented_no_abc(self):
        """
        Operation implemented without inheriting from the correct
        ABC -> Exception
        """

        class _BadDataSource(DataSource):
            """
            Implements get_by_id without inheriting from DetailGetter
            """

            def __init__(self) -> None:
                pass

            @property
            def attribute_types(self):
                raise NotImplementedError()

            @property
            def supported_types(self) -> list[str]:
                return ['uh-oh']

            def get_by_id(self, *args, **kwargs) -> None:
                raise Exception("shouldn't have made it this far!")

        bad_ds = _BadDataSource()
        rft = ReqFieldsTree('uh-oh', bad_ds)
        controller = Controller(bad_ds, DefaultView(rft), rft)

        with pytest.raises(UninheritedOperationError) as e:
            controller.get_detail('uh-oh', 'lol')

        error_str = str(e.value)
        assert '_BadDataSource' in error_str
        assert 'get_by_id' in error_str

    def test_get_recursive_relation(self):
        """
        `Controller().get_recursive_relation()` with found object.
        """

        mock_object = create_autospec(DataObject)
        type(mock_object).type = PropertyMock(return_value='test')

        expected = Mock()

        mock_view = create_autospec(View)
        mock_view.dump.return_value = expected

        mock_ds = create_autospec(Relational)
        mock_ds.get_recursive_relation.return_value = expected

        mock_rft = create_autospec(ReqFieldsTree)

        controller = Controller(mock_ds, mock_view, mock_rft)
        observed = controller.get_recursive_relation(mock_object, ['a', 'b'])

        mock_ds.validate_to_one_recurse.assert_called_once_with('test', ['a', 'b'])
        mock_ds.get_recursive_relation.assert_called_once_with(mock_object, ['a', 'b'])
        mock_view.dump.assert_called_once_with(expected)

        assert observed == expected

    def test_get_recursive_relation_not_found(self):
        """
        `Controller().get_recursive_relation()` doesn't find object
        -> raises `RecursiveRelationNotFoundException`.
        """

        mock_object = create_autospec(DataObject)
        type(mock_object).type = PropertyMock(return_value='test')

        mock_view = create_autospec(View)

        mock_ds = create_autospec(Relational)
        mock_ds.get_recursive_relation.return_value = None

        mock_rft = create_autospec(ReqFieldsTree)

        controller = Controller(mock_ds, mock_view, mock_rft)

        with pytest.raises(RecursiveRelationNotFoundException):
            controller.get_recursive_relation(mock_object, ['a', 'b'])

        mock_ds.validate_to_one_recurse.assert_called_once_with('test', ['a', 'b'])
        mock_ds.get_recursive_relation.assert_called_once_with(mock_object, ['a', 'b'])
        mock_view.dump.assert_not_called()

    def test_get_many_relations_page(self):
        """`Controller().get_many_relations_page()`"""

        expected = [Mock() for _ in range(3)]

        mock_object = create_autospec(DataObject)
        type(mock_object).type = PropertyMock(return_value='test')

        mock_view = create_autospec(View)
        mock_view.dump_bulk.side_effect = lambda i: i

        mock_params = Mock()
        type(mock_params).page = PropertyMock(return_value=3)
        type(mock_params).page_size = PropertyMock(return_value=5)

        mock_ds = create_autospec(Relational)
        mock_ds.get_to_many_relations_page.return_value = expected

        mock_rft = create_autospec(ReqFieldsTree)

        controller = Controller(mock_ds, mock_view, mock_rft)

        controller.get_many_relations_page(mock_object, 'test_relation', mock_params)

        mock_ds.get_to_many_relations_page.assert_called_once_with(
            mock_object, 'test_relation', 3, 5
        )
        mock_view.dump_bulk.assert_called_once_with(expected)
