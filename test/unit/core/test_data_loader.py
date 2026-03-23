# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List, Optional
from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    DataSource,
    DataSourceFilter,
    DefaultDataLoader,
    DefaultDataObjectToDataObjectConverter,
    GroupStatterDataLoader,
    IdsDataLoader,
    ObjectsDataLoader,
    core_data_object
)
from tol.core.operator import (
    ListGetter,
    Statter,
    Upserter
)


class _TestDataObjectToDataObjectConverter(DataObjectToDataObjectOrUpdateConverter):

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


class _MockDataSource(DataSource, Statter, ListGetter, Upserter):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.exhausted = False

    def get_list(self, object_type: str, object_filters: DataSourceFilter = None):
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

    def get_by_ids(
            self, object_type: str,
            object_ids: Iterable[str]) -> Iterable[Optional[DataObject]]:
        mock_objects = [
            {'id': 'test', 'attribute': 'att1'},
            {'id': 'test2', 'attribute': 'att2'}
        ]
        for obj in mock_objects:
            yield self.data_object_factory(
                type_=object_type,
                id_=obj.pop('id'),
                attributes=obj
            )

    def get_stats(
            self,
            object_type: str,
            stats_fields: List[str] = [],
            stats: List[str] = [],
            object_filters: DataSourceFilter = None
    ):
        pass

    def get_group_stats(
            self,
            object_type: str,
            group_by: List[str],
            stats_fields: List[str] = [],
            stats: List[str] = [],
            object_filters: DataSourceFilter = None
    ):
        if len(group_by) == 1:
            mock_objects = [
                {
                    'key': {'group_by_field': 'value1'},
                    'stats': {
                        'count': 3,
                        'field1': {
                            'min': 'A',
                            'max': 'Z'
                        },
                        'field2.attribute': {
                            'min': 'B',
                            'max': 'C'
                        }
                    }
                }, {
                    'key': {'group_by_field': 'value2'},
                    'stats': {
                        'count': 17,
                        'field1': {
                            'min': None,
                            'max': None
                        },
                        'field2.attribute': {
                            'min': None,
                            'max': None
                        }
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
                        'field1': {
                            'min': 'A',
                            'max': 'Z'
                        }
                    }
                }, {
                    'key': {'group_by_field1': 'value1',
                            'group_by_field2': 'valueY'},
                    'stats': {
                        'count': 17,
                        'field1': {
                            'min': None,
                            'max': None
                        }
                    }
                }, {
                    'key': {'group_by_field1': 'value2',
                            'group_by_field2': 'valueX'},
                    'stats': {
                        'count': 4,
                        'field1': {
                            'min': 'P',
                            'max': 'Q'
                        }
                    }
                }, {
                    'key': {'group_by_field1': 'value2',
                            'group_by_field2': 'valueY'},
                    'stats': {
                        'count': 200,
                        'field1': {
                            'min': None,
                            'max': None
                        }
                    }
                }
            ]
        yield from mock_objects

    def __record_exhaustion(self, objects):
        yield from objects
        self.exhausted = True

    def upsert(self, object_type, objects, provenance=None):
        objects_to_upsert = list(objects)
        # This is what we test with - make it it's own generator
        self.upserted = (obj for obj in objects_to_upsert)
        self.upserted_object_type = object_type
        return self.__record_exhaustion(objects_to_upsert)

    def insert(self, object_type, objects, provenance=None):
        objects_to_insert = list(objects)
        # This is what we test with - make it it's own generator
        self.inserted = (obj for obj in objects_to_insert)
        self.inserted_object_type = object_type
        return self.__record_exhaustion(objects_to_insert)

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

        upserted_objects = loader.load(auto_exhaust=False)
        # Test that the upserted objects have not been iterated through automatically
        assert not destination.exhausted
        for _ in upserted_objects:
            pass
        assert destination.exhausted

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
            convert_class=_TestDataObjectToDataObjectConverter
        )

        loader.load()
        # Test that the upserted objects have been iterated through automatically
        assert destination.exhausted

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

    def test_load_ids_and_convert(self):
        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        audit = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        core_data_object(audit)

        loader = IdsDataLoader(
            source=source,
            destination=destination,
            audit=audit,
            source_object_type='source_type',
            destination_object_type='destination_type',
            dependencies=[],
            loader_name='test_loader',
            object_ids=['test', 'test2'],
            convert_class=DefaultDataObjectToDataObjectConverter
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

    def test_load_objects_and_convert(self):
        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        audit = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        core_data_object(audit)

        loader = ObjectsDataLoader(
            source=None,
            destination=destination,
            audit=audit,
            source_object_type='source_type',
            destination_object_type='destination_type',
            dependencies=[],
            loader_name='test_loader',
            objects=source.get_list('source_type'),
            convert_class=DefaultDataObjectToDataObjectConverter
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
            group_statter_stats_fields=['field1', 'field2.attribute'],
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
        self.assertEqual('B', obj1.source_type_field2_attribute_min)
        self.assertEqual('C', obj1.source_type_field2_attribute_max)

        obj2 = next(destination.upserted)
        self.assertEqual('value2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual(17, obj2.source_type_count)
        self.assertIsNone(obj2.source_type_field1_min)
        self.assertIsNone(obj2.source_type_field1_max)
        self.assertIsNone(obj2.source_type_field2_attribute_min)
        self.assertIsNone(obj2.source_type_field2_attribute_max)

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
        self.assertEqual(3, obj1.source_type_valuex_count)
        self.assertEqual('A', obj1.source_type_field1_valuex_min)
        self.assertEqual('Z', obj1.source_type_field1_valuex_max)
        self.assertEqual(17, obj1.source_type_valuey_count)
        self.assertIsNone(obj1.source_type_field1_valuey_min)
        self.assertIsNone(obj1.source_type_field1_valuey_max)

        obj2 = next(destination.upserted)
        self.assertEqual('value2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual(4, obj2.source_type_valuex_count)
        self.assertEqual('P', obj2.source_type_field1_valuex_min)
        self.assertEqual('Q', obj2.source_type_field1_valuex_max)
        self.assertEqual(200, obj2.source_type_valuey_count)
        self.assertIsNone(obj2.source_type_field1_valuey_min)
        self.assertIsNone(obj2.source_type_field1_valuey_max)

        with self.assertRaises(StopIteration):
            next(destination.upserted)

    def test_load_insert_method(self):
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

        loader.load(method='insert')

        obj1 = next(destination.inserted)
        self.assertEqual('test', obj1.id)
        self.assertEqual('destination_type', obj1.type)
        self.assertEqual('att1', obj1.attribute)

        obj2 = next(destination.inserted)
        self.assertEqual('test2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual('att2', obj2.attribute)

        with self.assertRaises(StopIteration):
            next(destination.inserted)

        for obj in audit.upserted:
            self.assertEqual('test_loader', obj.id)
            self.assertEqual('data_load_event', obj.type)
            self.assertEqual('source_type', obj.source_object_type)
            self.assertEqual('destination_type', obj.destination_object_type)
