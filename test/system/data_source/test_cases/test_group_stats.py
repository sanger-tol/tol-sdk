# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from tol.core import (
    DataSourceFilter,
    OperableDataSource,
)

from ..dec import against
from ..fixtures import all_fixtures, api_elastic, elastic


class TestGroupStats:

    @against(*all_fixtures)
    def test_group_stats(self, data_source: OperableDataSource, ds_sleep):
        """
        Basic stats, without `union` or `cardinality`
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(
            data_source.get_by_ids('root', ids)
        )

        assert first == [None, None, None]

        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={'str_column': f'test_{id_}',
                            'int_column': i,
                            'datetime_column': datetime(2024, 1, i + 1, 0, 0, 0),
                            'bool_column': True if i % 2 == 0 else False,
                            'list_column': ['a', 'b', 'c'] if i == 0 else ['x', 'y', 'z']}
            )
            for i, id_ in enumerate(ids)
        ]

        data_source.upsert('root', data_objects)
        ds_sleep(5)  # Let Elastic settle down after the upsert

        stats = list(data_source.get_group_stats(
            'root',
            ['bool_column'],
            stats_fields=['int_column', 'datetime_column'],
            stats=['min', 'max', 'sum'],
            object_filters=None
        ))
        assert len(stats) == 2
        false_stats = stats[0]['stats']
        assert false_stats['count'] == 1
        assert false_stats['int_column']['min'] == 1
        assert false_stats['int_column']['max'] == 1
        assert false_stats['int_column']['sum'] == 1
        assert false_stats['datetime_column']['min'] == datetime(2024, 1, 2, 0, 0, 0)
        assert false_stats['datetime_column']['max'] == datetime(2024, 1, 2, 0, 0, 0)
        # Sum makes no sense for datetimes
        true_stats = stats[1]['stats']
        assert true_stats['count'] == 3
        assert true_stats['int_column']['min'] == 0
        assert true_stats['int_column']['max'] == 42
        assert true_stats['int_column']['sum'] == 44
        assert true_stats['datetime_column']['min'] == datetime(2020, 1, 1, 0, 0, 0)
        assert true_stats['datetime_column']['max'] == datetime(2024, 1, 3, 0, 0, 0)

        # Add another few to get more results for the second group_by
        ids = ['bill', 'bob', 'ben']
        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={'str_column': f'test_{id_}',
                            'int_column': i,
                            'datetime_column': datetime(2025, 1, i + 1, 0, 0, 0),
                            'bool_column': True if i % 2 == 0 else False,
                            'list_column': ['a', 'b', 'c'] if i == 0 else ['x', 'y', 'z']}
            )
            for i, id_ in enumerate(ids)
        ]
        data_source.upsert('root', data_objects)
        ds_sleep(5)  # Let Elastic settle down after the upsert

        stats = list(data_source.get_group_stats(
            'root',
            ['bool_column', 'int_column'],
            stats_fields=['datetime_column'],
            stats=['min', 'max'],
            object_filters=None
        ))
        assert len(stats) == 4
        false_stats = stats[0]['stats']
        assert false_stats['count'] == 2
        assert false_stats['datetime_column']['min'] == datetime(2024, 1, 2, 0, 0, 0)
        assert false_stats['datetime_column']['max'] == datetime(2025, 1, 2, 0, 0, 0)
        true_stats = stats[1]['stats']
        assert true_stats['count'] == 2
        assert true_stats['datetime_column']['min'] == datetime(2024, 1, 1, 0, 0, 0)
        assert true_stats['datetime_column']['max'] == datetime(2025, 1, 1, 0, 0, 0)
        true_stats = stats[2]['stats']
        assert true_stats['count'] == 2
        assert true_stats['datetime_column']['min'] == datetime(2024, 1, 3, 0, 0, 0)
        assert true_stats['datetime_column']['max'] == datetime(2025, 1, 3, 0, 0, 0)
        true_stats = stats[3]['stats']
        assert true_stats['count'] == 1
        assert true_stats['datetime_column']['min'] == datetime(2020, 1, 1, 0, 0, 0)
        assert true_stats['datetime_column']['max'] == datetime(2020, 1, 1, 0, 0, 0)

        # The following pattern is used in getting unique ids
        stats = list(data_source.get_group_stats(
            'root',
            ['int_column'],
            stats_fields=[],
            stats=[],
            object_filters=None
        ))
        assert len(stats) == 4
        assert stats[0]['key']['int_column'] == 0
        assert stats[1]['key']['int_column'] == 1
        assert stats[2]['key']['int_column'] == 2
        assert stats[3]['key']['int_column'] == 42

    @against(elastic, api_elastic)
    def test_group_stats_advanced(self, data_source: OperableDataSource, ds_sleep):
        """
        Advanced stats, only for (api ->) elastic, including `union` or `cardinality`
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(
            data_source.get_by_ids('root', ids)
        )

        assert first == [None, None, None]

        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={'str_column': f'test_{id_}',
                            'int_column': i,
                            'datetime_column': datetime(2024, 1, i + 1, 0, 0, 0),
                            'bool_column': True if i % 2 == 0 else False,
                            'list_column': ['a', 'b', 'c'] if i == 0 else ['x', 'y', 'z']}
            )
            for i, id_ in enumerate(ids)
        ]

        data_source.upsert('root', data_objects)
        ds_sleep(5)  # Let Elastic settle down after the upsert

        f = DataSourceFilter()
        f.and_ = {'datetime_column': {'gte': {'value': datetime(2021, 1, 1, 0, 0, 0)}}}
        stats = list(data_source.get_group_stats(
            'root',
            ['bool_column'],
            stats_fields=['list_column'],
            stats=['union'],
            object_filters=f
        ))
        assert len(stats) == 2
        false_stats = stats[0]['stats']
        assert false_stats['count'] == 1
        assert false_stats['list_column']['union'] == ['x', 'y', 'z']
        true_stats = stats[1]['stats']
        assert true_stats['count'] == 2
        assert true_stats['list_column']['union'] == ['a', 'b', 'c', 'x', 'y', 'z']

        # String min and max
        stats = list(data_source.get_group_stats(
            'root',
            ['bool_column'],
            stats_fields=['str_column'],
            stats=['min', 'max', 'unique', 'cardinality'],
            object_filters=f
        ))

        assert len(stats) == 2
        false_stats = stats[0]['stats']
        assert false_stats['count'] == 1
        assert false_stats['str_column']['min'] == 'test_train'
        assert false_stats['str_column']['max'] == 'test_train'
        assert false_stats['str_column']['unique'] == 1
        assert false_stats['str_column']['cardinality'] == 1
        true_stats = stats[1]['stats']
        assert true_stats['count'] == 2
        assert true_stats['str_column']['min'] == 'test_hype'
        assert true_stats['str_column']['max'] == 'test_max'
        assert true_stats['str_column']['unique'] == 2
        assert true_stats['str_column']['cardinality'] == 2
