# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import api_sql, sql


class TestToOneRelatedFiltering:
    """TOLP-8867"""

    @against(api_sql, sql)
    def test_filter_by_to_one_related_id(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        root_obj = data_source.data_object_factory(
            'root',
            '1',
            {
                'str_column': 'hello, world',
            }
        )
        data_source.upsert('root', [root_obj])

        related_objs = [
            data_source.data_object_factory(
                'related',
                c,
                {
                    'int_column': i,
                }
            )
            for i, c in enumerate('abc')
        ]
        data_source.upsert('related', related_objs)

    @against(api_sql, sql)
    def test_filter_by_to_related_attributes(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        pass
