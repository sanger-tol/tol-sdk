# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable

import pytest

from tol.api_base2.controller import Controller
from tol.api_base2.exception import (
    ObjectNotFoundByIdException,
    UnsupportedOpertionError
)
from tol.api_base2.misc import ListGetParamaters
from tol.api_base2.view import DefaultView
from tol.core import (
    CoreDataObject,
    ReadOnlyDataSource,
    unsupported
)


class _TestDataSource1(ReadOnlyDataSource):
    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass

    def get_by_id(self, object_type: str, object_ids: Iterable[str], *args, **kwargs):
        return [
            CoreDataObject(object_type, {'id': object_id})
            for object_id in object_ids
        ]

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @property
    def supported_types(self):
        return ['test2', 'test1']

    def get_attribute_types(self, object_type: str) -> Dict:
        raise NotImplementedError()


class _TestDataSource2(ReadOnlyDataSource):
    def get_list_page(self, object_type: str, *args, **kwargs):
        return [
            CoreDataObject(object_type, {'id': str(i)})
            for i in range(20)
        ], 20

    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @property
    def supported_types(self):
        return ['test_A', 'test_B']

    def get_attribute_types(self, object_type: str) -> Dict:
        return {}


class _TestDataSource3(ReadOnlyDataSource):
    """Accounts for page number and size in results"""

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        **kwargs
    ):
        return [
            CoreDataObject(
                object_type,
                {
                    'id': str(i + 1 + page_size * page_number),
                    'page_number': page_number,
                    'page_size': page_size
                }
            )
            for i in range(page_size)
        ], 560  # a very arbitrary number

    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

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

    def test_unsupported(self):
        """Unsupported method for mapped DataSource"""

        # DataSource1
        with pytest.raises(UnsupportedOpertionError):
            Controller(ds_1, DefaultView()).get_list('test1', ListGetParamaters({}))

        # DataSource2
        with pytest.raises(UnsupportedOpertionError):
            Controller(ds_2, DefaultView()).get_detail('test_B', 'anything goes')

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
            'page_number': '90',
            'page_size': '10'
        })
        expected = {
            'meta': {'total': 560,
                     'types': {}},
            'data': [
                {
                    'type': 'test_X',
                    'id': str(901 + i),
                    'attributes': {
                        'page_number': 90,
                        'page_size': 10
                    }
                }
                for i in range(10)
            ]
        }
        observed = controller.get_list('test_X', parsed)
        assert expected == observed
