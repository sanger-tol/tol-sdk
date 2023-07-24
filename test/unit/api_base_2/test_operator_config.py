# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base2.misc import DefaultOperatorConfig
from tol.core import DataSource
from tol.core.operator import (
    Aggregator,
    Deleter,
    DetailGetter,
    PageGetter,
    Updater,
    Upserter
)


class _MockDataSource1(
    DataSource,
    Aggregator,
    DetailGetter,
    PageGetter
):
    @property
    def supported_types(self):
        return ['a', 'b', 'c']

    def get_attribute_types(self, object_type: str):
        raise NotImplementedError()

    def get_aggregations(*args, **kwargs):
        raise NotImplementedError()

    def get_by_id(*args, **kwargs):
        raise NotImplementedError()

    def get_list_page(*args, **kwargs):
        raise NotImplementedError()


class _MockDataSource2(
    DataSource,
    Deleter,
    Updater,
    Upserter
):
    @property
    def supported_types(self):
        return ['4', '5', '6']

    def get_attribute_types(self, object_type: str):
        raise NotImplementedError()

    def delete(*args, **kwargs):
        raise NotImplementedError()

    def update(*args, **kwargs):
        raise NotImplementedError()

    def upsert(*args, **kwargs):
        raise NotImplementedError()


ds_1 = _MockDataSource1({})
ds_2 = _MockDataSource2({})


class TestDefaultOperatorConfig:
    def test_do_dict(self):
        """`DefaultOperatorConfig().to_dict()`"""

        expected_1 = {
            'noauth': [
                'aggregate',
                'detailGet',
                'listGet',
            ]
        }
        expected_2 = {
            'noauth': [
                'delete',
                'update',
                'upsert'
            ]
        }

        expected = {
            'a': expected_1,
            'b': expected_1,
            'c': expected_1,
            '4': expected_2,
            '5': expected_2,
            '6': expected_2
        }

        config = DefaultOperatorConfig(ds_1, ds_2)
        observed = config.to_dict()

        assert observed == expected
