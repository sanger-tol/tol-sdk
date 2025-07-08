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
                'related_object.id': {
                    'eq': {
                        'value': '1',
                    }
                },
                'int_column': {
                    'in_list': {
                        'value': [0, 42, 2099],
                    }
                }
            }
        )

        (root_obj,) = list(
            data_source.get_list('root', object_filters=f)
        )

        assert root_obj.id == 'a'
        assert root_obj.int_column == 0

    @against(sql, api_sql)
    def test_filter_by_to_one_related_id_and_attribute(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        self.__upsert_objs(data_source)

        f = DataSourceFilter(
            and_={
                'related_object.id': {
                    'lt': {
                        'value': '4'
                    }
                },
                'related_object.str_column': {
                    'eq': {
                        'value': 'hello, world'
                    }
                },
                'id': {
                    'in_list': {
                        'value': list('cyz')
                    }
                }
            }
        )

        (root_obj,) = list(
            data_source.get_list('root', f)
        )

        assert root_obj.id == 'c'
        assert root_obj.int_column == 2

    def __upsert_objs(
        self,
        data_source: OperableDataSource,
    ) -> None:

        related_obj = data_source.data_object_factory(
            'related',
            '1',
            {
                'str_column': 'hello, world',
            }
        )
        data_source.upsert('related', [related_obj])

        root_objs = [
            data_source.data_object_factory(
                'root',
                c,
                {
                    'int_column': i,
                },
                to_one={
                    'related_object': related_obj,
                },
            )
            for i, c in enumerate('abc')
        ]
        data_source.upsert('root', root_objs)
