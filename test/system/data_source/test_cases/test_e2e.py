# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Dict

import pytest

from tol.core import (
    DataSource,
    DataSourceError,
    DataSourceFilter,
    DefaultDataLoader,
    DefaultDataObjectToDataObjectConverter,
    OperableDataSource,
    core_data_object,
)
from tol.core.operator import ListGetter, RelationWriteMode, ReturnMode

from ..dec import against
from ..fixtures import all_fixtures
from ..fixtures.api.elastic import api_elastic
from ..fixtures.api.sql import api_sql
from ..fixtures.elastic_ds import elastic
from ..fixtures.sql_ds import sql


class _MockDataSource(DataSource, ListGetter):
    def __init__(self, config: Dict):
        super().__init__(config)

    def get_list(self, object_type: str, object_filters: DataSourceFilter):
        for i in range(150):
            yield self.data_object_factory(
                'source_type',
                f'loaded{i}',
                attributes={
                    'str_column': f'value{i}',
                    'bool_column': True,
                },
            )

    @property
    def supported_types(self):
        return ['source_type']


class TestEndToEnd:
    """
    Tests an end-to-end interaction on each given `DataSource`
    instance.
    """

    @against(sql, api_sql)
    def test_insert(self, data_source: OperableDataSource, ds_sleep):
        """
        Inserting works and does not permit duplicates.
        """

        objs = [
            data_source.data_object_factory(
                'root',
                f'id_{i}',
                attributes={'str_column': 'a' * i, 'int_column': ord(c)},
            )
            for i, c in enumerate('abc')
        ]

        # insert 3 different objects
        returned = data_source.insert('root', objs)

        if data_source.return_mode['root'] == ReturnMode.POPULATED:
            third = list(returned)[2]

            assert third.type == 'root'
            assert third.id == 'id_2'
            assert third.str_column == 'aa'
            assert third.int_column == 99

        # fail to insert the 2nd again
        with pytest.raises(DataSourceError):
            data_source.insert('root', [objs[1]])

        # get the 3rd
        fetched = data_source.get_one('root', 'id_2')
        assert fetched is not None

    @against(*all_fixtures)
    def test_upsert_and_detail_get(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert 3 `DataObject` instances, and get them by their IDs
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(data_source.get_by_ids('root', ids))

        assert first == [None, None, None]

        data_objects = [
            data_source.data_object_factory(
                'root', id_, attributes={'str_column': f'test_{id_}'}
            )
            for id_ in ids
        ]

        data_source.upsert('root', data_objects)
        ds_sleep(2)  # Let Elastic settle down after the upsert

        # they should all be present now
        second = list(data_source.get_by_ids('root', ids))

        assert len(second) == 3

        for id_, obj in zip(ids, second):
            assert obj.id == id_
            assert obj.str_column == f'test_{id_}'

        third = list(data_source.get_by_ids('root', ['train']))
        assert len(third) == 1
        assert third[0].id == 'train'
        assert third[0].str_column == 'test_train'

        # Test that get_one() also works!
        obj = data_source.get_one('root', 'max')
        assert obj.id == 'max'
        assert obj.str_column == 'test_max'

        fourth = list(data_source.get_by_ids('root', ['hokey', 'train', 'kokey']))
        assert len(fourth) == 3
        assert fourth[0] is None
        assert fourth[1].id == 'train'
        assert fourth[1].str_column == 'test_train'
        assert fourth[2] is None

    @against(*all_fixtures)
    def test_upsert_and_list_get(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert 3 `DataObject` instances, and get them as a list with filters
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(data_source.get_by_ids('root', ids))

        assert first == [None, None, None]

        related_objects = [
            data_source.data_object_factory(
                'related', str(i), attributes={'str_column': f'related_{i}'}
            )
            for i in range(len(ids))
        ]

        this_year = datetime.now().year
        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={
                    'str_column': f'test_{id_}',
                    'int_column': i,
                    'datetime_column': datetime(this_year - i, 1, 1),
                    'bool_column': True if i % 2 == 0 else False,
                    'list_column': [0, 1, 2] if i % 2 == 0 else [4, 5, 6],
                },
                to_one={'related_object': r_obj},
            )
            for i, (id_, r_obj) in enumerate(zip(ids, related_objects))
        ]

        if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
            data_source.upsert('related', related_objects)
        data_source.upsert('root', data_objects)

        ds_sleep(2)  # Let Elastic settle down after the upsert

        # they should all be present now
        second = list(data_source.get_list('root'))
        assert len(second) == 4  # These three plus the archetype

        # Exists filter
        f = DataSourceFilter()
        f.and_ = {'str_column': {'exists': {}}}
        third = list(data_source.get_list('root', object_filters=f))
        assert len(third) == 4  # These three plus the archetype

        # Not exists filter
        f = DataSourceFilter()
        f.and_ = {'str_column': {'exists': {'negate': True}}}
        fourth = list(data_source.get_list('root', object_filters=f))
        assert len(fourth) == 0

        # Date range
        f = DataSourceFilter()
        f.and_ = {
            'datetime_column': {
                'gte': {'value': f'{this_year - 1}-01-02'},
                'lt': {'value': f'{this_year}-01-03'},
            }
        }
        fifth = list(data_source.get_list('root', object_filters=f))
        assert len(fifth) == 1

        # Relative date
        f = DataSourceFilter()
        f.and_ = {
            'datetime_column': {
                'gte': {'value': 'one year ago'},
                'lt': {'value': 'now'},
            }
        }
        fifth2 = list(data_source.get_list('root', object_filters=f))
        assert len(fifth2) == 1

        # Datetime, rather than string
        f = DataSourceFilter()
        f.and_ = {
            'datetime_column': {
                'gte': {'value': datetime(this_year - 1, 1, 2)},
                'lt': {'value': datetime(this_year, 1, 3)},
            }
        }
        fifth3 = list(data_source.get_list('root', object_filters=f))
        assert len(fifth3) == 1

        # Boolean equal
        f = DataSourceFilter()
        f.and_ = {'bool_column': {'eq': {'value': True}}}
        sixth = list(data_source.get_list('root', object_filters=f))
        assert len(sixth) == 3  # Two of these plus the archetype

        # Int not equal
        f = DataSourceFilter()
        f.and_ = {'int_column': {'eq': {'value': 2, 'negate': True}}}
        seventh = list(data_source.get_list('root', object_filters=f))
        assert len(seventh) == 3  # Two of these plus the archetype

        # Str contains
        f = DataSourceFilter()
        f.and_ = {'str_column': {'contains': {'value': 'test_tra'}}}
        eighth = list(data_source.get_list('root', object_filters=f))
        assert len(eighth) == 1

        # Str not contains
        f = DataSourceFilter()
        f.and_ = {'str_column': {'contains': {'value': 'test_tra', 'negate': True}}}
        ninth = list(data_source.get_list('root', object_filters=f))
        assert len(ninth) == 3

        # Int in_list
        f = DataSourceFilter()
        f.and_ = {'int_column': {'in_list': {'value': [0, 2]}}}
        tenth = list(data_source.get_list('root', object_filters=f))
        assert len(tenth) == 2

        # Int not in_list
        f = DataSourceFilter()
        f.and_ = {'int_column': {'in_list': {'value': [0, 1, 2], 'negate': True}}}
        eleventh = list(data_source.get_list('root', object_filters=f))
        assert len(eleventh) == 1

        # Relationship field
        f = DataSourceFilter()
        f.and_ = {
            'related_object.str_column': {
                'in_list': {'value': ['related_1', 'related_2']}
            }
        }
        twelfth = list(data_source.get_list('root', object_filters=f))
        assert len(twelfth) == 2

        # List field equals
        f = DataSourceFilter()
        f.and_ = {'list_column': {'contains': {'value': 2}}}
        thirteenth = list(data_source.get_list('root', object_filters=f))
        assert len(thirteenth) == 2

        # List field not equals
        f = DataSourceFilter()
        f.and_ = {'list_column': {'contains': {'value': 2, 'negate': True}}}
        fourteenth = list(data_source.get_list('root', object_filters=f))
        assert len(fourteenth) == 2

        # Field to field string comparison
        f = DataSourceFilter()
        f.and_ = {
            'str_column': {'lt': {'field': 'related_object.str_column', 'negate': True}}
        }
        fifteenth = list(data_source.get_list('root', object_filters=f))
        assert len(fifteenth) == 4  # 3 plus the archetype

        # Field to field int comparison
        f = DataSourceFilter()
        f.and_ = {'int_column': {'eq': {'field': 'related_object.int_column'}}}
        sixteenth = list(data_source.get_list('root', object_filters=f))
        assert len(sixteenth) == 1  # The archetype

        # Field to field datetime comparison
        f = DataSourceFilter()
        f.and_ = {
            'related_object.datetime_column': {'gt': {'field': 'datetime_column'}}
        }
        seventeenth = list(data_source.get_list('root', object_filters=f))
        assert len(seventeenth) == 1  # The archetype

    @against(*all_fixtures)
    def test_multiple_upserts(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert a `DataObject` instance, and then upsert again to test upsert behaviour
        """

        obj1 = data_source.data_object_factory('root', '1', attributes={})
        data_source.upsert('root', [obj1])
        ds_sleep(2)  # Let Elastic settle down after the upsert

        # they should all be present now
        first = list(data_source.get_by_ids('root', ['1']))
        assert len(first) == 1
        ret = first[0]
        assert ret.str_column is None
        assert ret.int_column is None
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

        rel1 = data_source.data_object_factory(
            'related',
            'rel1',
            attributes={
                'str_column': 'value2',
                'int_column': 123,
            },
        )

        obj1 = data_source.data_object_factory(
            'root',
            '1',
            attributes={
                'str_column': 'test_2',
                'int_column': 2,
                'datetime_column': datetime(2024, 1, 2),
                'bool_column': False,
                'list_column': ['item1', 'item2'],
            },
            to_one={'related_object': rel1},
        )

        if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
            data_source.upsert('related', [rel1])
        returned_ = data_source.upsert('root', [obj1])

        if data_source.return_mode['root'] == ReturnMode.POPULATED:
            returned_root = list(returned_)[0]

            assert returned_root.id == '1'
            assert returned_root.str_column == 'test_2'
            assert returned_root.int_column == 2
            assert returned_root.datetime_column == datetime(2024, 1, 2)
            assert returned_root.bool_column is False
            assert returned_root.list_column == ['item1', 'item2']

        ds_sleep(2)  # Let Elastic settle down after the upsert

        second = list(data_source.get_by_ids('root', ['1']))
        assert len(second) == 1
        ret = second[0]
        assert ret.str_column == 'test_2'
        assert ret.int_column == 2
        assert ret.datetime_column == datetime(2024, 1, 2)
        assert ret.bool_column is False
        assert ret.list_column == ['item1', 'item2']
        assert ret.related_object.id == 'rel1'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 123
        assert ret.related_object.datetime_column is None
        assert ret.related_object.bool_column is None
        assert ret.related_object.list_column is None

        rel1 = data_source.data_object_factory(
            'related',
            'rel1',
            attributes={
                'int_column': 456,
                'bool_column': False,
                'datetime_column': datetime(2024, 6, 6),
            },
        )

        obj1 = data_source.data_object_factory(
            'root',
            '1',
            attributes={
                'int_column': 3,
                'datetime_column': datetime(2024, 1, 3),
                'bool_column': True,
                'list_column': ['item1', 'item3'],
            },
            to_one={'related_object': rel1},
        )

        if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
            data_source.upsert('related', [rel1])
        data_source.upsert('root', [obj1])

        ds_sleep(2)  # Let Elastic settle down after the upsert

        third = list(data_source.get_by_ids('root', ['1']))
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

        obj1 = data_source.data_object_factory('root', '1', attributes={})
        data_source.upsert('root', [obj1])
        ds_sleep(2)  # Let Elastic settle down after the upsert

        fourth = list(data_source.get_by_ids('root', ['1']))
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
            '1',
            attributes={
                'str_column': None,
                'int_column': None,
                'datetime_column': None,
                'bool_column': None,
                'list_column': None,
            },
            to_one={'related_object': None},
        )
        data_source.upsert('root', [obj1])
        ds_sleep(2)  # Let Elastic settle down after the upsert

        fifth = list(data_source.get_by_ids('root', ['1']))
        assert len(fifth) == 1
        ret = fifth[0]
        assert ret.str_column is None
        assert ret.int_column is None
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

    @against(sql, api_sql)
    def test_upsert_dict_attributes(self, data_source: OperableDataSource, ds_sleep):
        """
        Tests upserting and merging dict attributes seprately, since it is not
        yet implemented in the `ElasticDataSource`.

        Once `upsert()` is implemented for `SqlDataSource` dict merging should
        be tested for that too.
        """

        obj1 = data_source.data_object_factory('root', '1', attributes={})
        data_source.upsert('root', [obj1])
        ds_sleep(2)  # Let Elastic settle down after the upsert
        first = list(data_source.get_by_ids('root', ['1']))
        assert len(first) == 1
        ret = first[0]
        assert ret.dict_column is None

        obj1 = data_source.data_object_factory(
            'root',
            '1',
            attributes={
                'dict_column': {'key1': 6, 'key2': 7},
            },
        )
        returned_ = data_source.upsert('root', [obj1])

        if data_source.return_mode['root'] == ReturnMode.POPULATED:
            returned_root = list(returned_)[0]
            assert returned_root.dict_column == {'key1': 6, 'key2': 7}

        ds_sleep(2)  # Let Elastic settle down after the upsert
        second = list(data_source.get_by_ids('root', ['1']))
        assert len(second) == 1
        ret = second[0]
        assert ret.dict_column == {'key1': 6, 'key2': 7}

        obj1 = data_source.data_object_factory(
            'root',
            '1',
            attributes={
                'dict_column': {'key1': 8, 'key3': 9},
            },
        )
        returned_ = data_source.upsert('root', [obj1])

        if data_source.return_mode['root'] == ReturnMode.POPULATED:
            returned_root = list(returned_)[0]
            assert returned_root.dict_column == {'key1': 8, 'key2': 7, 'key3': 9}

        ds_sleep(2)  # Let Elastic settle down after the upsert
        third = list(data_source.get_by_ids('root', ['1']))
        assert len(third) == 1
        ret = third[0]
        assert ret.dict_column == {'key1': 8, 'key2': 7, 'key3': 9}

        obj1 = data_source.data_object_factory('root', '1', attributes={})
        data_source.upsert('root', [obj1])

        ds_sleep(2)  # Let Elastic settle down after the upsert
        fourth = list(data_source.get_by_ids('root', ['1']))
        assert len(fourth) == 1
        ret = fourth[0]
        assert ret.dict_column == {'key1': 8, 'key2': 7, 'key3': 9}

        obj1 = data_source.data_object_factory(
            'root',
            '1',
            attributes={
                'dict_column': None,
            },
            to_one={'related_object': None},
        )
        data_source.upsert('root', [obj1])
        ds_sleep(2)  # Let Elastic settle down after the upsert

        fifth = list(data_source.get_by_ids('root', ['1']))
        assert len(fifth) == 1
        ret = fifth[0]
        assert ret.dict_column is None

    @against(sql, api_sql)
    def test_upsert_no_merge_collections(self, data_source: OperableDataSource, ds_sleep):
        """
        Test that upserting with `merge_collections=False` does not merge collections
        """

        data_source.merge_collections = False
        obj1 = data_source.data_object_factory('root', '1', attributes={})

        obj1 = data_source.data_object_factory(
            'root',
            '11',
            attributes={
                'list_column': ['item1', 'item2'],
                'dict_column': {'key1': 6, 'key2': 7},
            },
        )
        data_source.upsert('root', [obj1])
        ds_sleep(2)  # Let Elastic settle down after the upsert

        first = list(data_source.get_by_ids('root', ['11']))
        assert len(first) == 1
        ret = first[0]
        assert ret.list_column == ['item1', 'item2']
        assert ret.dict_column == {'key1': 6, 'key2': 7}

        update = data_source.data_object_factory(
            'root',
            '11',
            attributes={
                'list_column': ['item3', 'item4'],
                'dict_column': {'key3': 8, 'key4': 9},
            },
        )
        data_source.upsert('root', [update], merge_collections=False)
        ds_sleep(2)  # Let Elastic settle down after the upsert

        second = list(data_source.get_by_ids('root', ['11']))
        assert len(second) == 1
        ret = second[0]
        assert ret.list_column == ['item3', 'item4']
        assert ret.dict_column == {'key3': 8, 'key4': 9}

    @against(elastic, api_elastic)
    def test_elastic_no_merge_collection(self, data_source: OperableDataSource, ds_sleep):
        obj1 = data_source.data_object_factory(
            'root',
            '1',
            attributes={'str_column': 'testy'},
        )
        with pytest.raises(DataSourceError):
            data_source.upsert('root', [obj1], merge_collections=False)

    @against(elastic)  # `Updater` not implemented on `Api`- or `SqlDataSource`
    def test_update(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert a `DataObject` instance, and then perform updates
        """
        obj1 = data_source.data_object_factory(
            'root',
            '1',
            attributes={'str_column': 'test_2'},
        )
        rel1 = data_source.data_object_factory(
            'related',
            'rel1',
            attributes={
                'str_column': 'value2',
                'int_column': 123,
            },
        )
        rel2 = data_source.data_object_factory(
            'related',
            'rel2',
            attributes={
                'int_column': 456,
                'bool_column': False,
                'datetime_column': datetime(2024, 6, 6),
            },
        )
        data_source.upsert('root', [obj1])
        data_source.upsert('related', [rel1, rel2])
        ds_sleep(2)
        # they should all be present now
        first = list(data_source.get_by_ids('root', ['1']))
        assert len(first) == 1
        ret = first[0]
        assert ret.str_column == 'test_2'
        assert ret.int_column is None
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

        # Update with ID given
        update = (
            None,
            {
                'str_column': 'test_2',
                'int_column': 2,
                'datetime_column': datetime(2024, 1, 2),
                'bool_column': False,
                'related_object': rel1,
                'list_column': ['item1', 'item2'],
            },
        )
        data_source.update(
            'root',
            [update],
            candidate_key=['str_column'],
        )
        ds_sleep(2)
        second = list(data_source.get_by_ids('root', ['1']))
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
        update = (
            None,
            {
                'int_column': 2,
                'datetime_column': datetime(2024, 1, 3),
                'bool_column': True,
                'related_object': rel2,
                'list_column': ['item1', 'item3'],
            },
        )
        data_source.update('root', [update], candidate_key=['int_column'])
        ds_sleep(2)
        third = list(data_source.get_by_ids('root', ['1']))
        assert len(third) == 1
        ret = third[0]
        assert ret.str_column == 'test_2'  # Should not have changed
        assert ret.int_column == 2
        assert ret.datetime_column == datetime(2024, 1, 3)
        assert ret.bool_column is True
        assert ret.related_object.id == 'rel2'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 456
        assert ret.related_object.datetime_column == datetime(2024, 6, 6)
        assert ret.related_object.bool_column is False
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2', 'item3']

        update = (None, {'int_column': 2})
        data_source.update('root', [update], candidate_key=['int_column'])
        ds_sleep(2)
        fourth = list(data_source.get_by_ids('root', ['1']))
        assert len(fourth) == 1
        ret = fourth[0]
        assert ret.str_column == 'test_2'  # Should not have changed
        assert ret.int_column == 2
        assert ret.datetime_column == datetime(2024, 1, 3)
        assert ret.bool_column is True
        assert ret.related_object.id == 'rel2'
        assert ret.related_object.str_column == 'value2'
        assert ret.related_object.int_column == 456
        assert ret.related_object.datetime_column == datetime(2024, 6, 6)
        assert ret.related_object.bool_column is False
        assert ret.related_object.list_column is None
        assert ret.list_column == ['item1', 'item2', 'item3']

        update = (
            None,
            {
                'str_column': None,
                'int_column': 2,
                'datetime_column': None,
                'bool_column': None,
                'related_object': None,
                'list_column': None,
            },
        )
        data_source.update('root', [update], candidate_key=['int_column'])
        ds_sleep(5)
        fifth = list(data_source.get_by_ids('root', ['1']))
        assert len(fifth) == 1
        ret = fifth[0]
        assert ret.str_column is None
        assert ret.int_column == 2
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

        update = (
            None,
            {
                'str_column': 'Updated by function',
                'int_column': 2,
                'datetime_column': None,
                'bool_column': None,
                'related_object': None,
                'list_column': None,
            },
        )
        data_source.update(
            'root', [update], candidate_key_func=lambda x: ['int_column']
        )
        ds_sleep(5)
        sixth = list(data_source.get_by_ids('root', ['1']))
        assert len(sixth) == 1
        ret = sixth[0]
        assert ret.str_column == 'Updated by function'
        assert ret.int_column == 2
        assert ret.datetime_column is None
        assert ret.bool_column is None
        assert ret.related_object is None
        assert ret.list_column is None

    @against(*all_fixtures)
    def test_count(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert a `DataObject` instance, and then count
        """
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'str_column': f'test_{id_}',
                    'bool_column': True if id_ % 2 == 0 else False,
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects)
        ds_sleep(2)

        cnt = data_source.get_count('root')
        assert cnt == 11  # The archetype plus the new 10

        # Count with filter
        f = DataSourceFilter()
        f.and_ = {'str_column': {'in_list': {'value': ['test_4', 'test_6', 'test_7']}}}

        cnt = data_source.get_count('root', object_filters=f)
        assert cnt == 3

        # Count with filter on runtime field
        f = DataSourceFilter()
        f.and_ = {'runtime_column': {'eq': {'value': True}}}

        cnt = data_source.get_count('root', object_filters=f)
        assert cnt == 5

    @against(elastic, api_elastic)
    def test_stats(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert 3 `DataObject` instances, and get them as a list with filters
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(data_source.get_by_ids('root', ids))

        assert first == [None, None, None]

        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={
                    'str_column': f'test_{id_}',
                    'int_column': i,
                    'datetime_column': datetime(2024, 1, i + 1, 0, 0, 0),
                    'bool_column': True if i % 2 == 0 else False,
                    'list_column': ['a', 'b', 'c'] if i == 0 else ['x', 'y', 'z'],
                },
            )
            for i, id_ in enumerate(ids)
        ]

        data_source.upsert('root', data_objects)
        ds_sleep(5)  # Let Elastic settle down after the upsert

        stats = data_source.get_stats(
            'root',
            stats_fields=['bool_column', 'datetime_column', 'int_column'],
            stats=['min', 'max', 'sum', 'unique', 'cardinality'],
            object_filters=None,
        )['stats']
        # Min makes no sense for bools
        # Max makes no sense for bools
        # Sum makes no sense for bools
        assert stats['bool_column']['unique'] == 2
        assert stats['bool_column']['cardinality'] == 2
        assert stats['datetime_column']['min'] == datetime(2020, 1, 1, 0, 0, 0)
        assert stats['datetime_column']['max'] == datetime(2024, 1, 3, 0, 0, 0)
        # Sum makes no sense for datetimes
        assert stats['datetime_column']['unique'] == 4
        assert stats['datetime_column']['cardinality'] == 4
        assert stats['int_column']['min'] == 0
        assert stats['int_column']['max'] == 42
        assert stats['int_column']['sum'] == 45
        assert stats['int_column']['unique'] == 4
        assert stats['int_column']['cardinality'] == 4

    @against(elastic)
    def test_runtime_fields(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert a `DataObject` instance, and then query a runtime field
        """
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'str_column': f'test_{id_}',
                    'bool_column': True if id_ % 2 == 0 else False,
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects)
        ds_sleep(2)

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2']))
        assert len(first) == 2
        ret = first[0]
        assert ret.runtime_column is True
        ret = first[1]
        assert ret.runtime_column is False

        # Get list by runtime field query
        f = DataSourceFilter()
        f.and_ = {'runtime_column': {'eq': {'value': True}}}
        second = list(data_source.get_list('root', object_filters=f))
        assert len(second) == 5

        # Get list page by runtime field query
        third, _ = data_source.get_list_page('root', 1, object_filters=f, page_size=20)
        assert len(list(third)) == 5

        # Get list and check runtime field
        f = DataSourceFilter()
        f.and_ = {'bool_column': {'eq': {'value': True}}}
        fourth = list(data_source.get_list('root', object_filters=f))
        assert len(fourth) == 6  # 5 plus archetype
        assert fourth[0].runtime_column is False
        assert fourth[1].runtime_column is False
        assert fourth[2].runtime_column is False
        assert fourth[3].runtime_column is False
        assert fourth[4].runtime_column is False
        assert fourth[5].runtime_column is False

    @against(*all_fixtures)
    def test_data_loader(self, data_source: OperableDataSource, ds_sleep):
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        loader = DefaultDataLoader(
            source=mock_ds,
            destination=data_source,
            source_object_type='source_type',
            destination_object_type='root',
            dependencies=[],
            convert_class=DefaultDataObjectToDataObjectConverter,
            loader_name='e2e loader',
        )
        loader.load(provenance='e2e')
        ds_sleep(5)

        f = DataSourceFilter()
        f.and_ = {'str_column': {'eq': {'value': 'abc', 'negate': True}}}
        loaded = list(data_source.get_list('root', object_filters=f))
        assert len(loaded) == 150
