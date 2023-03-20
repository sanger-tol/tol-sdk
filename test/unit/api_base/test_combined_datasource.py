# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base.datasource import CombinedDataSource
from tol.core import DataSource, unsupported


class _TestDataSource1(DataSource):  # noqa

    count = 0

    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    def get_list_page(self, *args, **kwargs):
        self.count += 1


class _TestDataSource2(DataSource):  # noqa

    count = 0

    def get_by_id(self, *args, **kwargs):
        self.count += 1

    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass


ds_1 = _TestDataSource1({})
ds_2 = _TestDataSource2({})

combined_ds = CombinedDataSource(
    {
        'species': {
            'object_type': 'species',
            'data_source': ds_1
        },
        'specimen': {
            'object_type': 'specimen',
            'data_source': ds_1
        },
        'samples': {
            'object_type': 'samples',
            'data_source': ds_2
        },
    }
)


class TestCombinedDataSource:
    def test_supported_methods(self):
        assert combined_ds.operation_is_supported_for_type(
            'specimen',
            'get_by_id'
        ) is False
        assert combined_ds.operation_is_supported_for_type(
            'species',
            'get_by_id'
        ) is False
        assert combined_ds.operation_is_supported_for_type(
            'samples',
            'get_by_id'
        ) is True

        assert combined_ds.operation_is_supported_for_type(
            'specimen',
            'get_list_page'
        ) is True
        assert combined_ds.operation_is_supported_for_type(
            'species',
            'get_list_page'
        ) is True
        assert combined_ds.operation_is_supported_for_type(
            'samples',
            'get_list_page'
        ) is False
