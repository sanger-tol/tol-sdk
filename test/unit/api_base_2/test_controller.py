# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable
from unittest.mock import MagicMock

import pytest

from tol.api_base2.controller import Controller
from tol.api_base2.exception import (
    ObjectNotFoundByIdException,
    UnsupportedOpertionError
)
from tol.api_base2.misc import (
    AggregationBody,
    AggregationParameters,
    ListGetParamaters
)
from tol.api_base2.view import DefaultView
from tol.core import (
    DataSource,
    DataSourceFilter,
    core_data_object
)
from tol.core.abc import Aggregator, DetailGetter, PageGetter


CoreDataObject = core_data_object()  # noqa


class _TestDataSource1(DataSource, DetailGetter):

    def get_by_id(self, object_type: str, object_ids: Iterable[str], *args, **kwargs):
        return [
            CoreDataObject(object_type, {'id': object_id})
            for object_id in object_ids
        ]

    @property
    def supported_types(self):
        return ['test2', 'test1']

    def get_attribute_types(self, object_type: str) -> Dict:
        raise NotImplementedError()


class _TestDataSource2(DataSource, PageGetter):
    def get_list_page(self, object_type: str, *args, **kwargs):
        return [
            CoreDataObject(object_type, {'id': str(i)})
            for i in range(20)
        ], 20

    @property
    def supported_types(self):
        return ['test_A', 'test_B']

    def get_attribute_types(self, object_type: str) -> Dict:
        return {}


class _TestDataSource3(DataSource, Aggregator, PageGetter):
    """Accounts for page number and size in results"""

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
        **kwargs
    ):
        return [
            CoreDataObject(
                object_type,
                {
                    'id': str(i + 1 + page_size * page_number),
                    'page': page_number,
                    'page_size': page_size,
                    'filter': object_filters.exact['column1'],
                    'sort_by': sort_by
                }
            )
            for i in range(page_size)
        ], 560  # a very arbitrary number

    def get_aggregations(
            self,
            object_type: str,
            aggregations: Dict,
            object_filters: DataSourceFilter = None
    ) -> Dict:
        return {
            'completed_over_time': {
                'buckets': [
                    {
                        'key_as_string': '2015-04-01T00:00:00.000Z',
                        'key': 1427846400000,
                        'doc_count': 3
                    },
                    {
                        'key_as_string': '2015-05-01T00:00:00.000Z',
                        'key': 1430438400000,
                        'doc_count': 0
                    },
                ]
            }
        }

    @property
    def supported_types(self):
        return ['test_X']

    def get_attribute_types(self, object_type: str) -> Dict:
        return {}


ds_1 = _TestDataSource1({})
ds_2 = _TestDataSource2({})
ds_3 = _TestDataSource3({})


class TestController:
    def test_good_object_type(self):
        expected = {
            'meta': {'total': 20,
                     'types': {}},
            'data': [
                {
                    'type': 'test_B',
                    'id': str(i)
                }
                for i in range(20)
            ]
        }
        controller = Controller(ds_2, DefaultView())
        observed = controller.get_list('test_B', ListGetParamaters({}))
        assert observed == expected

    def test_not_found(self):
        """DataSource().get_by_id() returning [None] (no elements) causes 404 error"""

        class _TestDataSourceNotFound(_TestDataSource1):
            def get_by_id(self, *args, **kwargs):
                return [None]

        not_found_ds = _TestDataSourceNotFound({})

        controller = Controller(not_found_ds, DefaultView())

        with pytest.raises(ObjectNotFoundByIdException):
            controller.get_detail('test2', 'anything goes too')

    def test_page_size_and_number(self):
        """Check that page_size and page_number are passed in correctly"""

        controller = Controller(ds_3, DefaultView())
        parsed = ListGetParamaters({
            'page': '90',
            'page_size': '10',
            'filter': """
                {"exact": {"column1": "value1"}}
            """,
            'sort_by': '-column1'
        })
        expected = {
            'meta': {'total': 560,
                     'types': {}},
            'data': [
                {
                    'type': 'test_X',
                    'id': str(901 + i),
                    'attributes': {
                        'page': 90,
                        'page_size': 10,
                        'filter': 'value1',
                        'sort_by': '-column1'

                    }
                }
                for i in range(10)
            ]
        }
        observed = controller.get_list('test_X', parsed)
        assert expected == observed

    def test_aggregations(self):
        """Check that aggregations are working"""

        controller = Controller(ds_3, DefaultView())
        parsed = AggregationParameters({
            'filter': """
                {"exact": {"column1": "value1"}}
            """
        })
        body = AggregationBody({
            'aggs': {
                'completed_over_time': {
                    'date_histogram': {
                        'field': 'complete_date',
                        'calendar_interval': 'month'
                    }
                }
            }
        })
        expected = {
            'meta': {
                'aggregations': {'completed_over_time': {
                    'buckets': [
                        {
                            'key_as_string': '2015-04-01T00:00:00.000Z',
                            'key': 1427846400000,
                            'doc_count': 3
                        },
                        {
                            'key_as_string': '2015-05-01T00:00:00.000Z',
                            'key': 1430438400000,
                            'doc_count': 0
                        },
                    ]}},
                'types': {}},
            'data': []
        }
        observed = controller.post_aggregations('test_X', parsed, body)
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

            def get_attribute_types(self, object_type: str) -> Dict:
                raise NotImplementedError()

            @property
            def supported_types(self) -> list[str]:
                return ['no']

        bad_ds = _BadDataSource()
        controller = Controller(bad_ds, DefaultView())

        with pytest.raises(UnsupportedOpertionError):
            controller.get_detail('test', 'hype')
        with pytest.raises(UnsupportedOpertionError):
            controller.get_list('test')
        with pytest.raises(UnsupportedOpertionError):
            controller.post_aggregations(
                'test',
                MagicMock(),
                MagicMock()
            )
