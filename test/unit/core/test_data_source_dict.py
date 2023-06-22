# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict

import pytest

from tol.core import (
    ReadOnlyDataSource,
    core_data_object,
    unsupported
)
from tol.core.data_source_dict import DataSourceDict
from tol.core.datasource_error import UnknownObjectTypeException


CoreDataObject = core_data_object()  # noqa


class _TestDataSource1(ReadOnlyDataSource):
    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass

    def get_by_id(self, object_type: str, object_id: str, *args, **kwargs):
        return [
            CoreDataObject(object_type, {'id': object_id})
        ]

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @unsupported
    def get_aggregations(self, *args, **kwargs):
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
        ]

    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @unsupported
    def get_aggregations(self, *args, **kwargs):
        pass

    @property
    def supported_types(self):
        return ['test_A', 'test_B']

    def get_attribute_types(self, object_type: str) -> Dict:
        raise NotImplementedError()


ds_1 = _TestDataSource1({})
ds_2 = _TestDataSource2({})


class TestDataSourceDict:
    def test_known_type_keys(self):
        """Use keys that are registered to one of the given DataSource"""
        d = DataSourceDict(ds_1, ds_2)

        assert d['test1'] == ds_1
        assert d['test2'] == ds_1
        assert d['test_A'] == ds_2
        assert d['test_B'] == ds_2

    def test_unkown_type_keys(self):
        """
        Keys that are not registered to any DataSource raise
        UnknownObjectTypeException
        """
        d = DataSourceDict(ds_2, ds_1)

        with pytest.raises(UnknownObjectTypeException):
            d['this-is_']
        with pytest.raises(UnknownObjectTypeException):
            d['soooooo RANDOM!!!']
