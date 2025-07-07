# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import api_sql, sql


class TestToOneRelatedFiltering:
    """TOLP-8867"""

    @against(sql, api_sql)
    def test_filter_by_to_one_related_id(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        self.__upsert_objs(data_source)

        f = DataSourceFilter(
            and_={
                'my_root.id': {
                    'eq': {
                        'value': '1'
                    }
                },
                'str_column': {
                    'int_column': {
                        'value': [0, 42, 2099]
                    }
                }
            }
        )

        (rel_obj, ) = list(
            data_source.get_list('related', f)
        )

        assert rel_obj.id == 'a'
        assert rel_obj.int_column == 0

    @against(sql, api_sql)
    def test_filter_by_to_one_related_attribute(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        self.__upsert_objs(data_source)

        f = DataSourceFilter(
            and_={
                'my_root.str_column': {
                    'eq': {
                        'value': 'hello, world'
                    }
                },
                'id': {
                    'int_column': {
                        'value': list('cyz')
                    }
                }
            }
        )

        (rel_obj, ) = list(
            data_source.get_list('related', f)
        )

        assert rel_obj.id == 'c'
        assert rel_obj.int_column == 2

    def __upsert_objs(
        self,
        data_source: OperableDataSource,
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
