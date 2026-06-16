# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    DummyRecordToElasticRecordConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['record', 'category', 'sub_category']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_record = RelationshipConfig()
        rc_record.to_one = {
            'category': 'category',
            'sub_category': 'sub_category',
        }
        return {'record': rc_record}

    def get_to_one_relation(
            self,
            source: DataObject,
            relationship_name: str
    ):
        pass

    def get_to_many_relations(
            self,
            source: DataObject,
            relationship_name: str
    ):
        raise NotImplementedError()


class TestDummyRecordToElasticRecordConverter(TestCase):
    def test_converter(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source, destination)

        category = source.data_object_factory(
            type_='category',
            id_='cat2'
        )
        sub_category = source.data_object_factory(
            type_='sub_category',
            id_='cat1'
        )

        converter = DummyRecordToElasticRecordConverter(
            data_object_factory=destination.data_object_factory,
            config=DummyRecordToElasticRecordConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='1',
            type_='record',
            attributes={
                'little_string': 'a',
                'big_string': 'b',
                'int': 1,
            },
            to_one={
                'category': category,
                'sub_category': sub_category,
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)

        self.assertEqual(ret1.id, '1')
        self.assertEqual(ret1.type, 'record')
        self.assertEqual(ret1.attributes['little_string'], 'a')
        self.assertEqual(ret1.attributes['big_string'], 'b')
        self.assertEqual(ret1.attributes['int'], 1)
        self.assertEqual(ret1.category.id, 'cat2')
        self.assertEqual(ret1.sub_category.id, 'cat1')

        with self.assertRaises(StopIteration):
            next(converteds)

    def test_converter_without_id(self):

        destination = _MockDataSourceRelational(config={})
        core_data_object(destination)
        converter = DummyRecordToElasticRecordConverter(
            data_object_factory=destination.data_object_factory,
            config=DummyRecordToElasticRecordConverter.Config()
        )

        obj = destination.data_object_factory(
            id_=None,
            type_='record',
            attributes={
                'little_string': 'a',
            }
        )

        converteds = converter.convert(obj)
        with self.assertRaises(StopIteration):
            next(converteds)
