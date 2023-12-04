# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable
from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataObjectToDataObjectConverter,
    DataSource,
    DataSourceFilter,
    DefaultDataLoader,
    DefaultDataObjectToDataObjectConverter,
    GroupCounterDataLoader,
    core_data_object
)
from tol.core.operator import (
    ListGetter,
    Upserter
)


class TestDataObjectToDataObjectConverter(DataObjectToDataObjectConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        CoreDataObject = self._data_object_factory # noqa N806
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


class _MockDataSource(DataSource, ListGetter, Upserter):
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

    def get_counts(self, object_type: str, group_by: str,
                   object_filters: DataSourceFilter):
        mock_objects = [{'value1': 3},
                        {'value2': 17}]
        for obj in mock_objects:
            yield obj

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
            destination_object_type='source_type',
            dependencies=[],
            convert_class=DefaultDataObjectToDataObjectConverter,
            loader_name='test_loader'
        )

        loader.load()

        obj1 = next(destination.upserted)
        self.assertEqual('test', obj1.id)
        self.assertEqual('source_type', obj1.type)
        self.assertEqual('att1', obj1.attribute)

        obj2 = next(destination.upserted)
        self.assertEqual('test2', obj2.id)
        self.assertEqual('source_type', obj2.type)
        self.assertEqual('att2', obj2.attribute)

        with self.assertRaises(StopIteration):
            next(destination.upserted)

        for obj in audit.upserted:
            self.assertEqual('test_loader', obj.id)
            self.assertEqual('data_load_event', obj.type)
            self.assertEqual('source_type', obj.source_object_type)
            self.assertEqual('source_type', obj.destination_object_type)

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

    def test_load_group_counts(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        audit = _MockDataSource(config={})
        core_data_object(source, destination, audit)

        loader = GroupCounterDataLoader(
            source=source,
            destination=destination,
            audit=audit,
            source_object_type='source_type',
            destination_object_type='destination_type',
            dependencies=[],
            group_counter_group_by='test',
            loader_name='test_loader'
        )

        loader.load()

        obj1 = next(destination.upserted)
        self.assertEqual('value1', obj1.id)
        self.assertEqual('destination_type', obj1.type)
        self.assertEqual(3, obj1.source_type_count)

        obj2 = next(destination.upserted)
        self.assertEqual('value2', obj2.id)
        self.assertEqual('destination_type', obj2.type)
        self.assertEqual(17, obj2.source_type_count)

        with self.assertRaises(StopIteration):
            next(destination.upserted)
