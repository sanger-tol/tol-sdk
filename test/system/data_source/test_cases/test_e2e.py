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
                            'bool_column': True if i % 2 == 0 else False,
                            'related_object': {'id': i, 'str_column': f'related_{i}'},
                            'list_column': [0, 1, 2] if i % 2 == 0 else [4, 5, 6]}
            )
            for i, id_ in enumerate(ids)
        ]

        data_source.upsert('root', data_objects)
        time.sleep(2)  # Let Elastic settle down after the upsert

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
        f.and_ = {'str_column': [{'op': 'exists', 'negate': True}]}
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
            {'op': 'eq', 'value': 2, 'negate': True}
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

        # Str not contains
        f = DataSourceFilter()
        f.and_ = {'str_column': [
            {'op': 'contains', 'value': 'test_tra', 'negate': True}
        ]}
        ninth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(ninth) == 3

        # Int in_list
        f = DataSourceFilter()
        f.and_ = {'int_column': [
            {'op': 'in_list', 'value': [0, 2]}
        ]}
        tenth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(tenth) == 2

        # Int not in_list
        f = DataSourceFilter()
        f.and_ = {'int_column': [
            {'op': 'in_list', 'value': [0, 1, 2], 'negate': True}
        ]}
        eleventh = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(eleventh) == 1

        # Relationship field
        f = DataSourceFilter()
        f.and_ = {'related_object.str_column': [
            {'op': 'in_list', 'value': ['related_1', 'related_2']}
        ]}
        twelfth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(twelfth) == 2

        # List field equals
        f = DataSourceFilter()
        f.and_ = {'list_column': [
            {'op': 'eq', 'value': 2}
        ]}
        thirteenth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(thirteenth) == 2

        # List field equals
        f = DataSourceFilter()
        f.and_ = {'list_column': [
            {'op': 'eq', 'value': 2, 'negate': True}
        ]}
        fourteenth = list(
            data_source.get_list('root', object_filters=f)
        )
        assert len(fourteenth) == 2

    @against(elastic)  # list and dict columns not implemented on SqlDataSource
    def test_upsert(self, data_source: OperableDataSource):
        """
        Upsert a `DataObject` instance, and then upsert again to test upsert behaviour
        """
        obj1 = data_source.data_object_factory(
            'root',
            1,
            attributes={}
        )
        data_source.upsert('root', [obj1])

        # they should all be present now
        first = list(
            data_source.get_by_id('root', [1])
        )
        assert len(first) == 1
        ret = first[0]
        assert ret.str_column is None
        assert ret.int_column is None
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

        obj1 = data_source.data_object_factory(
            'root',
            1,
            attributes={'str_column': 'test_2',
                        'int_column': 2,
                        'datetime_column': datetime(2024, 1, 2),
                        'bool_column': False,
                        'related_object': {
                            'id': 'rel1',
                            'str_column': 'value2',
                            'int_column': 123},
                        'list_column': ['item1', 'item2']}
        )
        data_source.upsert('root', [obj1])

        second = list(
            data_source.get_by_id('root', [1])
        )
        assert len(second) == 1
        ret = second[0]
        assert ret.str_column == 'test_2'
        assert ret.int_column == 2
        assert ret.datetime_column == datetime(2024, 1, 2)
        assert ret.bool_column is False
        assert ret.related_object.id == 'rel1'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 123
        assert ret.related_object.datetime_column is None
        assert ret.related_object.bool_column is None
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2']

        obj1 = data_source.data_object_factory(
            'root',
            1,
            attributes={'int_column': 3,
                        'datetime_column': datetime(2024, 1, 3),
                        'bool_column': True,
                        'related_object': {
                            'id': 'rel1',
                            'int_column': 456,
                            'bool_column': False,
                            'datetime_column': datetime(2024, 6, 6)
                        },
                        'list_column': ['item1', 'item3']}
        )
        data_source.upsert('root', [obj1])

        third = list(
            data_source.get_by_id('root', [1])
        )
        assert len(third) == 1
        ret = third[0]
        assert ret.str_column == 'test_2'  # Should not have changed
        assert ret.int_column == 3
        assert ret.datetime_column == datetime(2024, 1, 3)
        assert ret.bool_column is True
        assert ret.related_object.id == 'rel1'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 456
        assert ret.related_object.datetime_column == datetime(2024, 6, 6)
        assert ret.related_object.bool_column is False
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2', 'item3']

        obj1 = data_source.data_object_factory(
            'root',
            1,
            attributes={}
        )
        data_source.upsert('root', [obj1])

        fourth = list(
            data_source.get_by_id('root', [1])
        )
        assert len(fourth) == 1
        ret = fourth[0]
        assert ret.str_column == 'test_2'  # Should not have changed
        assert ret.int_column == 3
        assert ret.datetime_column == datetime(2024, 1, 3)
        assert ret.bool_column is True
        assert ret.related_object.id == 'rel1'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 456
        assert ret.related_object.datetime_column == datetime(2024, 6, 6)
        assert ret.related_object.bool_column is False
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2', 'item3']

        obj1 = data_source.data_object_factory(
            'root',
            1,
            attributes={'str_column': None,
                        'int_column': None,
                        'datetime_column': None,
                        'bool_column': None,
                        'related_object': None,
                        'list_column': None}
        )
        data_source.upsert('root', [obj1])

        fifth = list(
            data_source.get_by_id('root', [1])
        )
        assert len(fifth) == 1
        ret = fifth[0]
        assert ret.str_column is None
        assert ret.int_column is None
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

    @against(elastic)  # list and dict columns not implemented on SqlDataSource
    def test_update(self, data_source: OperableDataSource):
        """
        Upsert a `DataObject` instance, and then perform updates
        """
        obj1 = data_source.data_object_factory(
            'root',
            1,
            attributes={'str_column': 'test_2'}
        )
        data_source.upsert('root', [obj1])
        time.sleep(2)
        # they should all be present now
        first = list(
            data_source.get_by_id('root', [1])
        )
        assert len(first) == 1
        ret = first[0]
        assert ret.str_column == 'test_2'
        assert ret.int_column is None
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

        # Update with ID given
        update = (None, {
            'str_column': 'test_2',
            'int_column': 2,
            'datetime_column': datetime(2024, 1, 2),
            'bool_column': False,
            'related_object': {
                'id': 'rel1',
                'str_column': 'value2',
                'int_column': 123},
            'list_column': ['item1', 'item2']
        })
        data_source.update('root', [update],
                           candidate_key=['str_column'])
        time.sleep(2)
        second = list(
            data_source.get_by_id('root', [1])
        )
        assert len(second) == 1
        ret = second[0]
        assert ret.str_column == 'test_2'
        assert ret.int_column == 2
        assert ret.datetime_column == datetime(2024, 1, 2)
        assert ret.bool_column is False
        assert ret.related_object.id == 'rel1'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 123
        assert ret.related_object.datetime_column is None
        assert ret.related_object.bool_column is None
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2']

        # Update by candidate key
        update = (None, {
            'int_column': 2,
            'datetime_column': datetime(2024, 1, 3),
            'bool_column': True,
            'related_object': {
                'id': 'rel1',
                'int_column': 456,
                'bool_column': False,
                'datetime_column': datetime(2024, 6, 6)
            },
            'list_column': ['item1', 'item3']}
        )
        data_source.update('root', [update],
                           candidate_key=['int_column'])
        time.sleep(2)
        third = list(
            data_source.get_by_id('root', [1])
        )
        assert len(third) == 1
        ret = third[0]
        assert ret.str_column == 'test_2'  # Should not have changed
        assert ret.int_column == 2
        assert ret.datetime_column == datetime(2024, 1, 3)
        assert ret.bool_column is True
        assert ret.related_object.id == 'rel1'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 456
        assert ret.related_object.datetime_column == datetime(2024, 6, 6)
        assert ret.related_object.bool_column is False
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2', 'item3']

        update = (None, {'int_column': 2})
        data_source.update('root', [update],
                           candidate_key=['int_column'])
        time.sleep(2)
        fourth = list(
            data_source.get_by_id('root', [1])
        )
        assert len(fourth) == 1
        ret = fourth[0]
        assert ret.str_column == 'test_2'  # Should not have changed
        assert ret.int_column == 2
        assert ret.datetime_column == datetime(2024, 1, 3)
        assert ret.bool_column is True
        assert ret.related_object.id == 'rel1'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 456
        assert ret.related_object.datetime_column == datetime(2024, 6, 6)
        assert ret.related_object.bool_column is False
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2', 'item3']

        update = (None, {
            'str_column': None,
            'int_column': 2,
            'datetime_column': None,
            'bool_column': None,
            'related_object': None,
            'list_column': None}
        )
        data_source.update('root', [update],
                           candidate_key=['int_column'])
        time.sleep(5)
        fifth = list(
            data_source.get_by_id('root', [1])
        )
        assert len(fifth) == 1
        ret = fifth[0]
        assert ret.str_column is None
        assert ret.int_column == 2
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

    @against(elastic)
    def test_count(self, data_source: OperableDataSource):
        """
        Upsert a `DataObject` instance, and then count
        """
        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={'str_column': f'test_{id_}'}
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects)
        time.sleep(2)

        cnt = data_source.get_count('root')
        assert cnt == 11  # The archetype plus the new 10

        f = DataSourceFilter()
        f.and_ = {'str_column': [{
            'op': 'in_list',
            'value': ['test_4', 'test_6', 'test_7']
        }]}

        cnt = data_source.get_count('root', object_filters=f)
        assert cnt == 3

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

        f = DataSourceFilter()
        f.and_ = {'datetime_column': [{'op': 'gte', 'value': datetime(2021, 1, 1, 0, 0, 0)}]}
        stats = list(data_source.get_stats(
            object_type='root',
            group_by='bool_column',
            stats_fields=['list_column'],
            stats=['union'],
            object_filters=f
        ))
        assert len(stats) == 2
        false_stats = next(iter(stats[0].values()))
        assert false_stats['count'] == 1
        assert false_stats['list_column_union'] == ['x', 'y', 'z']
        true_stats = next(iter(stats[1].values()))
        assert true_stats['count'] == 2
        assert true_stats['list_column_union'] == ['a', 'b', 'c', 'x', 'y', 'z']
