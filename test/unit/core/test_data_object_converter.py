# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest import (TestCase)
from unittest.mock import PropertyMock, create_autospec

from tol.core import (
    DataLoader,
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    DataSource,
    DefaultDataObjectToDataObjectConverter,
    core_data_object
)


class _TestDataObjectToDataObjectConverter(DataObjectToDataObjectOrUpdateConverter):

    def convert(
        self,
        data_object: DataObject
    ) -> Iterable[DataObject]:
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


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['source_type', 'destination_type']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestDataObjectConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        mock_dl = create_autospec(DataLoader)
        type(mock_dl)._destination_object_type = PropertyMock(
            return_value='destination_type'
        )
        converter = DefaultDataObjectToDataObjectConverter(
            data_object_factory=destination.data_object_factory
        )
        converter.data_loader = mock_dl

        CoreDataObject = source.data_object_factory  # noqa N806
        # if data_object relations data = data else data.attributes
        obj1 = CoreDataObject(
            id_='test1',
            type_='source_type',
            attributes={'attribute1': 'value1'}
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='source_type',
            attributes={'attribute1': 'value2'}
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual('destination_type', ret1.type)
        self.assertEqual(obj1.attributes, ret1.attributes)

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert_iterable([obj1, obj2])
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual('destination_type', ret1.type)
        self.assertEqual(obj1.attributes, ret1.attributes)

        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual('destination_type', ret2.type)
        self.assertEqual(obj2.attributes, ret2.attributes)

        with self.assertRaises(StopIteration):
            next(converteds)

    def test_convert_with_multiple_converted_from_one_input(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = _TestDataObjectToDataObjectConverter(
            data_object_factory=destination.data_object_factory
        )
        CoreDataObject = source.data_object_factory  # noqa N806
        # if data_object relations data = data else data.attributes
        obj1 = CoreDataObject(
            id_='test1',
            type_='source_type',
            attributes={'attribute1': 'value1'}
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='source_type',
            attributes={'attribute1': 'value2'}
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(f'{obj1.id}_test', ret1.id)
        self.assertEqual('destination_type', ret1.type)
        self.assertEqual({**obj1.attributes,
                          'other_attribute': 'other_value'}, ret1.attributes)

        ret2 = next(converteds)
        self.assertEqual(f'{obj1.id}_test2', ret2.id)
        self.assertEqual('destination_type', ret2.type)
        self.assertEqual({**obj1.attributes,
                          'other_attribute2': 'other_value2'}, ret2.attributes)

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert_iterable([obj1, obj2])
        ret1 = next(converteds)
        self.assertEqual(f'{obj1.id}_test', ret1.id)
        self.assertEqual('destination_type', ret1.type)
        self.assertEqual({**obj1.attributes,
                          'other_attribute': 'other_value'}, ret1.attributes)

        ret2 = next(converteds)
        self.assertEqual(f'{obj1.id}_test2', ret2.id)
        self.assertEqual('destination_type', ret2.type)
        self.assertEqual({**obj1.attributes,
                          'other_attribute2': 'other_value2'}, ret2.attributes)

        ret3 = next(converteds)
        self.assertEqual(f'{obj2.id}_test', ret3.id)
        self.assertEqual('destination_type', ret3.type)
        self.assertEqual({**obj2.attributes,
                          'other_attribute': 'other_value'}, ret3.attributes)

        ret4 = next(converteds)
        self.assertEqual(f'{obj2.id}_test2', ret4.id)
        self.assertEqual('destination_type', ret4.type)
        self.assertEqual({**obj2.attributes,
                          'other_attribute2': 'other_value2'}, ret4.attributes)

        with self.assertRaises(StopIteration):
            next(converteds)

    def test_convert_with_id_field(self):
        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        mock_dl = create_autospec(DataLoader)
        type(mock_dl)._destination_object_type = PropertyMock(
            return_value='destination_type'
        )
        converter = DefaultDataObjectToDataObjectConverter(
            data_object_factory=destination.data_object_factory,
            id_field='id_field'
        )
        converter.data_loader = mock_dl
        CoreDataObject = source.data_object_factory  # noqa N806

        obj1 = CoreDataObject(
            id_='test1',
            type_='source_type',
            attributes={
                'attribute1': 'value1',
                'id_field': 'test1_id'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.attributes['id_field'], ret1.id)
        self.assertEqual('destination_type', ret1.type)
        # Asserts that the id_field is not included in the attributes
        self.assertEqual({k: v for k, v in obj1.attributes.items() if k != 'id_field'},
                         ret1.attributes)
        self.assertNotIn('id_field', ret1.attributes)
