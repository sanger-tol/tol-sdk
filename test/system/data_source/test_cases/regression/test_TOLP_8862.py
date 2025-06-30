# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource

from ...dec import against
from ...fixtures import api_sql, sql


class TestTOLP_8862:

    @against(api_sql, sql)
    def test_filter_by_int_id(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        objs = [
            data_source.data_object_factory(
                'inc',
                id_=str(i),
            )
            for i in range(3)
        ]
        data_source.upsert('inc', objs)

        f = DataSourceFilter(
            and_={
                'id': {'gt': {'value': 0}, 'lt': {'value': 2}}
            }
        )
        (fetched, ) = list(data_source.get_list('inc', object_filters=f))

        assert fetched.id == '1'

    @against(api_sql, sql)
    def test_filter_by_str_id(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        objs = [
            data_source.data_object_factory(
                'root',
                id_=c,
            )
            for c in 'abc'
        ]
        data_source.upsert('root', objs)

        f = DataSourceFilter(
            and_={
                'id': {'gt': {'value': 'a'}, 'lt': {'value': 'c'}}
            }
        )
        (fetched, ) = list(data_source.get_list('root', object_filters=f))

        assert fetched.id == 'b'
