# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import api_sql, sql


class TestMultipleToOneFiltering:
    """TOLP-8861"""

    @against(sql, api_sql)
    def test_filter_by_two_to_one_relationships(
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
                'another_related.str_column': {
                    'in_list': {
                        'value': [
                            'hello to you too',
                        ]
                    }
                }
            }
        )

        (root_obj,) = list(
            data_source.get_list(
                'root',
                object_filters=f,
                requested_fields=['id', 'int_column', 'another_related.str_column'],
            )
        )

        assert root_obj.id == '1'
        assert root_obj.int_column == 1
        assert root_obj.another_related.str_column == 'hello to you too'

    def __upsert_objs(
        self,
        data_source: OperableDataSource,
    ) -> None:

        first_related_obj = data_source.data_object_factory(
            'related',
            '1',
            {
                'str_column': 'hello, world',
            }
        )
        second_related_obj = data_source.data_object_factory(
            'related',
            '2',
            {
                'str_column': 'hello to you too'
            }
        )
        data_source.upsert(
            'related',
            [first_related_obj, second_related_obj],
        )

        first_root_obj = data_source.data_object_factory(
            'root',
            '1',
            {
                'int_column': 1,
            },
            to_one={
                'related_object': first_related_obj,
                'another_related': second_related_obj,
            },
        )
        second_root_obj = data_source.data_object_factory(
            'root',
            '2',
            {
                'int_column': 2,
            },
            to_one={
                'another_related': second_related_obj,
            },
        )
        data_source.upsert(
            'root',
            [first_root_obj, second_root_obj],
        )
