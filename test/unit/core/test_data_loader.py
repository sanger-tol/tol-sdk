# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List
from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataObjectToDataObjectConverter,
    DataSource,
    DataSourceFilter,
    DefaultDataLoader,
    DefaultDataObjectToDataObjectConverter,
    GroupStatterDataLoader,
    core_data_object
)
from tol.core.operator import (
    GroupStatter,
    ListGetter,
    Upserter
)


class TestDataObjectToDataObjectConverter(DataObjectToDataObjectConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        CoreDataObject = self._data_object_factory  # noqa N806
        # if data_object relations data = data else data.attributes
        ret1 = CoreDataObject(
            id_=f'{data_object.id}_test',
            type_='destination_type',
            attributes={**data_object.attributes, 'other_attribute': 'other_value'}
        )
        ret2 = CoreDataObject(
            id_=f'{data_object.id}_test2',
            type_='destination_type',
            attributes={**data_object.attributes, 'other_attribute2': 'other_value2'}
        )
        return iter([ret1, ret2])


class _MockDataSource(DataSource, GroupStatter, ListGetter, Upserter):
    def __init__(self, config: Dict):
        super().__init__(config)

    def get_list(self, object_type: str, object_filters: DataSourceFilter):
        if object_filters is not None:
            mock_objects = [{'id': 'test', 'attribute': 'att1'}]
        else:
            mock_objects = [{'id': 'test', 'attribute': 'att1'},
                            {'id': 'test2', 'attribute': 'att2'}]
        for obj in mock_objects:
            yield self.data_object_factory(
                type_=object_type,
                id_=obj.pop('id'),
                attributes=obj
            )

    def get_stats(self, object_type: str, group_by: List[str],
                  stats_fields: List[str] = [],
                  stats: List[str] = [],
                  object_filters: DataSourceFilter = None):
        if len(group_by) == 1:
            mock_objects = [
                {
                    'key': {'group_by_field': 'value1'},
                    'stats': {
                        'count': 3,
                        'field1_min': 'A',
                        'field1_max': 'Z'
                    }
                }, {
                    'key': {'group_by_field': 'value2'},
                    'stats': {
                        'count': 17,
                        'field1_min': None,
                        'field1_max': None
                    }
                }
            ]
        else:
            mock_objects = [
                {
                    'key': {'group_by_field1': 'value1',
                            'group_by_field2': 'valueX'},
                    'stats': {
                        'count': 3,
                        'field1_min': 'A',
                        'field1_max': 'Z'
                    }
                }, {
                    'key': {'group_by_field1': 'value1',
                            'group_by_field2': 'valueY'},
                    'stats': {
                        'count': 17,
                        'field1_min': None,
                        'field1_max': None
                    }
                }, {
                    'key': {'group_by_field1': 'value2',
                            'group_by_field2': 'valueX'},
                    'stats': {
                        'count': 4,
                        'field1_min': 'P',
                        'field1_max': 'Q'
                    }
                }, {
                    'key': {'group_by_field1': 'value2',
                            'group_by_field2': 'valueY'},
                    'stats': {
                        'count': 200,
                        'field1_min': None,
                        'field1_max': None
                    }
                }
            ]
        yield from mock_objects

    def upsert(self, object_type, objs, field_prefix=None):
        self.upserted = objs
        self.upserted_object_type = object_type

    @property
    def supported_types(self):
        return [
            'source_type',
            'destination_type',
            'data_load_event'
        ]


class TestDataLoader(TestCase):
    def test_load_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        audit = _MockDataSource(config={})
        core_data_object(source, destination, audit)

        loader = DefaultDataLoader(
            source=source,
            destination=destination,
            audit=audit,
            source_object_type='source_type',
            destination_object_type='destination_type',
            dependencies=[],
            convert_class=DefaultDataObjectToDataObjectConverter,
            loader_name='test_loader'
        )

        loader.load()

        obj1 = next(destination.upserted)
        self.assertEqual('test', obj1.id)
        self.assertEqual('destination_type', obj1.type)
        self.assertEqual('att1', obj1.attribute)

        obj2 = next(destination.upserted)
        self.assertEqual('test2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual('att2', obj2.attribute)

        with self.assertRaises(StopIteration):
            next(destination.upserted)

        for obj in audit.upserted:
            self.assertEqual('test_loader', obj.id)
            self.assertEqual('data_load_event', obj.type)
            self.assertEqual('source_type', obj.source_object_type)
            self.assertEqual('destination_type', obj.destination_object_type)

    def test_load_with_filter_and_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        audit = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        core_data_object(audit)

        object_filters = DataSourceFilter()
        object_filters.exact = {'id': 10}

        loader = DefaultDataLoader(
            source=source,
            destination=destination,
            audit=audit,
            source_object_type='source_type',
            destination_object_type='destination_type',
            dependencies=[],
            loader_name='test_loader',
            object_filters=object_filters,
            convert_class=TestDataObjectToDataObjectConverter
        )

        loader.load()

        obj1 = next(destination.upserted)
        self.assertEqual('test_test', obj1.id)
        self.assertEqual('destination_type', obj1.type)
        self.assertEqual('att1', obj1.attribute)
        self.assertEqual('other_value', obj1.other_attribute)

        obj2 = next(destination.upserted)
        self.assertEqual('test_test2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual('att1', obj2.attribute)
        self.assertEqual('other_value2', obj2.other_attribute2)

        with self.assertRaises(StopIteration):
            next(destination.upserted)

        for obj in audit.upserted:
            self.assertEqual('test_loader', obj.id)
            self.assertEqual('data_load_event', obj.type)
            self.assertEqual('source_type', obj.source_object_type)
            self.assertEqual('destination_type', obj.destination_object_type)

    def test_load_group_stats_one_group_by(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        audit = _MockDataSource(config={})
        core_data_object(source, destination, audit)

        loader = GroupStatterDataLoader(
            source=source,
            destination=destination,
            audit=audit,
            source_object_type='source_type',
            destination_object_type='destination_type',
            dependencies=[],
            group_statter_group_by=['group_by_field'],
            group_statter_stats_fields=['field1'],
            group_statter_stats=['min', 'max'],
            loader_name='test_loader'
        )

        loader.load()

        obj1 = next(destination.upserted)
        self.assertEqual('value1', obj1.id)
        self.assertEqual('destination_type', obj1.type)
        self.assertEqual(3, obj1.source_type_count)
        self.assertEqual('A', obj1.source_type_field1_min)
        self.assertEqual('Z', obj1.source_type_field1_max)

        obj2 = next(destination.upserted)
        self.assertEqual('value2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual(17, obj2.source_type_count)
        self.assertIsNone(obj2.source_type_field1_min)
        self.assertIsNone(obj2.source_type_field1_max)

        with self.assertRaises(StopIteration):
            next(destination.upserted)

    def test_load_group_stats_two_group_bys(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        audit = _MockDataSource(config={})
        core_data_object(source, destination, audit)

        loader = GroupStatterDataLoader(
            source=source,
            destination=destination,
            audit=audit,
            source_object_type='source_type',
            destination_object_type='destination_type',
            dependencies=[],
            group_statter_group_by=['group_by_field1', 'group_by_field2'],
            group_statter_stats_fields=['field1'],
            group_statter_stats=['min', 'max'],
            loader_name='test_loader'
        )

        loader.load()

        obj1 = next(destination.upserted)
        self.assertEqual('value1', obj1.id)
        self.assertEqual('destination_type', obj1.type)
        self.assertEqual(3, obj1.source_type_valueX_count)
        self.assertEqual('A', obj1.source_type_valueX_field1_min)
        self.assertEqual('Z', obj1.source_type_valueX_field1_max)
        self.assertEqual(17, obj1.source_type_valueY_count)
        self.assertIsNone(obj1.source_type_valueY_field1_min)
        self.assertIsNone(obj1.source_type_valueY_field1_max)

        obj2 = next(destination.upserted)
        self.assertEqual('value2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual(4, obj2.source_type_valueX_count)
        self.assertEqual('P', obj2.source_type_valueX_field1_min)
        self.assertEqual('Q', obj2.source_type_valueX_field1_max)
        self.assertEqual(200, obj2.source_type_valueY_count)
        self.assertIsNone(obj2.source_type_valueY_field1_min)
        self.assertIsNone(obj2.source_type_valueY_field1_max)

        with self.assertRaises(StopIteration):
            next(destination.upserted)
