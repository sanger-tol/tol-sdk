# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    ErrorObject,
    core_data_object
)
from tol.core.operator import Relational
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    BenchlingTissueToBenchlingWorklistItemConverterFactory
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['tissue', 'worklist', 'worklist_item']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_worklist_item = RelationshipConfig()
        rc_worklist_item.to_one = {
            'worklist': 'worklist',
            'item': 'tissue'
        }
        return {'worklist_item': rc_worklist_item}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        raise NotImplementedError()

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestBenchlingTissueToStsSampleConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)

        CoreDataObject = source.data_object_factory  # noqa N806

        obj1 = CoreDataObject(
            id_='test1',
            type_='tissue',
            attributes={}
        )
        worklist = CoreDataObject(
            id_='worklist1',
            type_='worklist',
            attributes={
                'name': 'Worklist 1',
            }
        )
        obj2 = ErrorObject(
            details='test_detail',
            object_type='test_type',
            object_=obj1,
        )

        converter_class = \
            BenchlingTissueToBenchlingWorklistItemConverterFactory(worklist).get_converter_class()
        converter = converter_class(
            data_object_factory=destination.data_object_factory
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertIsNone(ret1.id)
        self.assertEqual('worklist_item', ret1.type)
        self.assertEqual(ret1.worklist.id, 'worklist1')
        self.assertEqual(ret1.item.id, 'test1')

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        assert isinstance(ret2, ErrorObject)

        with self.assertRaises(StopIteration):
            next(converteds)
