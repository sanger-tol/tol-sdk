# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import time
from datetime import datetime

from tol.core import (
    DataSourceFilter,
    OperableDataSource
)

from ..dec import against
from ..fixtures import all_fixtures
from ..fixtures.api.elastic import api_elastic
from ..fixtures.elastic_ds import elastic


class TestEndToEnd:
    """
    Tests an end-to-end interaction on each given `DataSource`
    instance.
    """

    @against(*all_fixtures)
    def test_upsert_and_detail_get(self, data_source: OperableDataSource):
        """
        Upsert 3 `DataObject` instances, and get them by their IDs
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(
            data_source.get_by_id('root', ids)
        )

        assert first == [None, None, None]

        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={'str_column': f'test_{id_}'}
            )
            for id_ in ids
        ]

        data_source.upsert('root', data_objects)

        # they should all be present now
        second = list(
            data_source.get_by_id('root', ids)
        )

        assert len(second) == 3

        for id_, obj in zip(ids, second):
            assert obj.id == id_
            assert obj.str_column == f'test_{id_}'

    @against(elastic, api_elastic)  # and_ filter not yet implemented on SqlDataSource
    def test_upsert_and_list_get(self, data_source: OperableDataSource):
        """
        Upsert 3 `DataObject` instances, and get them as a list with filters
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(
            data_source.get_by_id('root', ids)
        )

        assert first == [None, None, None]

        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={'str_column': f'test_{id_}',
                            'int_column': i,
                            'datetime_column': datetime(2024, 1, i + 1),
                            'bool_column': True if i % 2 == 0 else False}
            )
            for i, id_ in enumerate(ids)
        ]

        data_source.upsert('root', data_objects)
        time.sleep(5)  # Let Elastic settle down after the upsert

        # they should all be present now
        second = list(
            data_source.get_list('root')
        )
        assert len(second) == 4  # These three plus the archetype

        # Exists filter
        f = DataSourceFilter()
        f.and_ = {'str_column': [{'op': 'exists'}]}
        third = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(third) == 4  # These three plus the archetype

        # Not exists filter
        f = DataSourceFilter()
        f.and_ = {'str_column': [{'op': 'not_exists'}]}
        fourth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(fourth) == 0

        # Date range
        f = DataSourceFilter()
        f.and_ = {'datetime_column': [
            {'op': 'gte', 'value': '2024-01-02'},
            {'op': 'lt', 'value': '2024-01-03'}
        ]}
        fifth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(fifth) == 1

        # Boolean equal
        f = DataSourceFilter()
        f.and_ = {'bool_column': [
            {'op': 'eq', 'value': True}
        ]}
        sixth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(sixth) == 3  # Two of these plus the archetype

        # Int not equal
        f = DataSourceFilter()
        f.and_ = {'int_column': [
            {'op': 'neq', 'value': 2}
        ]}
        seventh = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(seventh) == 3  # Two of these plus the archetype

        # Str contains
        f = DataSourceFilter()
        f.and_ = {'str_column': [
            {'op': 'contains', 'value': 'test_tra'}
        ]}
        eighth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(eighth) == 1

        # Int in_list
        f = DataSourceFilter()
        f.and_ = {'int_column': [
            {'op': 'in_list', 'value': [0, 2]}
        ]}
        ninth = list(
            data_source.get_list('root', object_filters=f)
        )

        assert len(ninth) == 2

    @against(elastic)
    def test_group_statter(self, data_source: OperableDataSource):
        """
        Upsert 3 `DataObject` instances, and get them as a list with filters
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(
            data_source.get_by_id('root', ids)
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
        time.sleep(5)  # Let Elastic settle down after the upsert

        stats = list(data_source.get_stats(
            object_type='root',
            group_by='bool_column',
            stats_fields=['int_column', 'datetime_column'],
            stats=['min', 'max', 'sum'],
            object_filters=None
        ))
        assert len(stats) == 2
        false_stats = next(iter(stats[0].values()))
        assert false_stats['count'] == 1
        assert false_stats['int_column_min'] == 1
        assert false_stats['int_column_max'] == 1
        assert false_stats['int_column_sum'] == 1
        assert false_stats['datetime_column_min'] == datetime(2024, 1, 2, 0, 0, 0)
        assert false_stats['datetime_column_max'] == datetime(2024, 1, 2, 0, 0, 0)
        # Sum makes no sense for datetimes
        true_stats = next(iter(stats[1].values()))
        assert true_stats['count'] == 3
        assert true_stats['int_column_min'] == 0
        assert true_stats['int_column_max'] == 42
        assert true_stats['int_column_sum'] == 44
        assert true_stats['datetime_column_min'] == datetime(2020, 1, 1, 0, 0, 0)
        assert true_stats['datetime_column_max'] == datetime(2024, 1, 3, 0, 0, 0)

        stats = list(data_source.get_stats(
            object_type='root',
            group_by='bool_column',
            stats_fields=['list_column'],
            stats=['union'],
            object_filters=None
        ))
        assert len(stats) == 2
        false_stats = next(iter(stats[0].values()))
        assert false_stats['count'] == 1
        assert false_stats['list_column_union'] == ['x', 'y', 'z']
        true_stats = next(iter(stats[1].values()))
        assert true_stats['count'] == 3
        assert true_stats['list_column_union'] == ['a', 'b', 'c', 'x', 'y', 'z']
