# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter
from tol.sql import SqlDataSource


class TestGroupStats:
    """One grouping and one stat at a time."""

    def test_min(self, sql_ds: SqlDataSource) -> None:
        self.__insert_gs_objs(sql_ds)

        observed = sql_ds.get_group_stats(
            'gs',
            group_by=['str_column'],
            stats_fields=['int_column'],
            stats=['min'],
            object_filters=self.__gs_filters,
        )

        expected = [
            {
                'key': {
                    'str_column': 'same',
                },
                'stats': {
                    'int_column': {
                        'min': 1
                    }
                }
            }
        ]

        assert observed == expected

    def test_max(self, sql_ds: SqlDataSource) -> None:
        self.__insert_gs_objs(sql_ds)

        observed = sql_ds.get_group_stats(
            'gs',
            group_by=['str_column'],
            stats_fields=['int_column'],
            stats=['max'],
            object_filters=self.__gs_filters,
        )

        expected = [
            {
                'key': {
                    'str_column': 'same',
                },
                'stats': {
                    'int_column': {
                        'max': 2
                    }
                }
            }
        ]

        assert observed == expected

    def test_sum(self, sql_ds: SqlDataSource) -> None:
        self.__insert_gs_objs(sql_ds)

        observed = sql_ds.get_group_stats(
            'gs',
            group_by=['str_column'],
            stats_fields=['int_column'],
            stats=['sum'],
            object_filters=self.__gs_filters,
        )

        expected = [
            {
                'key': {
                    'str_column': 'same',
                },
                'stats': {
                    'int_column': {
                        # =1+2
                        'sum': 3
                    }
                }
            }
        ]

        assert observed == expected

    def test_unique(self, sql_ds: SqlDataSource) -> None:
        pass

    def test_cardinality(self, sql_ds: SqlDataSource) -> None:
        pass

    def test_union(self, sql_ds: SqlDataSource) -> None:
        self.__insert_gs_objs(sql_ds)

        observed = sql_ds.get_group_stats(
            'gs',
            group_by=['str_column'],
            stats_fields=['list_column'],
            stats=['union'],
            object_filters=self.__gs_filters,
        )

        expected = [
            {
                'key': {
                    'str_column': 'same',
                },
                'stats': {
                    'list_column': {
                        'union': [1, 2, 3]
                    }
                }
            }
        ]

        assert observed == expected

    def test_count(self, sql_ds: SqlDataSource) -> None:
        self.__insert_gs_objs(sql_ds)

        observed = sql_ds.get_group_stats(
            'gs',
            group_by=['str_column'],
            stats_fields=['int_column'],
            stats=['count'],
            object_filters=self.__gs_filters,
        )

        expected = [
            {
                'key': {
                    'str_column': 'same',
                },
                'stats': {
                    'int_column': {
                        'count': 2
                    }
                }
            }
        ]

        assert observed == expected

    def __insert_gs_objs(self, sql_ds: SqlDataSource) -> None:
        objs = (
            sql_ds.data_object_factory(
                'gs',
                str(i),
                {
                    'int_column': i,
                    'str_column': 'same',
                    'list_column': [i, i + 1],
                }
            )
            for i in range(3)
        )

        sql_ds.insert_batch('gs', objs)

    @property
    def __gs_filters(self) -> DataSourceFilter:
        return DataSourceFilter(
            and_={
                'int_column': {
                    'gt': {
                        'value': 0
                    }
                }
            }
        )
