# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
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
    StsBankedSampleToElasticSampleConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['banked_sample', 'banked_sample_category']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_banked_sample = RelationshipConfig()
        rc_banked_sample.to_one = {
            'category': 'banked_sample_category'
        }
        return {'banked_sample': rc_banked_sample}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.id == 'test1':
            return source._host.data_object_factory(
                id_='test1',
                type_='banked_sample_category',
                attributes={'name': 'category1'}
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestStsSpeciesToElasticSpeciesConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsBankedSampleToElasticSampleConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        banked_sample_category = CoreDataObject(
            id_='test1',
            type_='banked_sample_category',
            attributes={'name': 'category1'}
        )
        obj1 = CoreDataObject(
            id_='test1',
            type_='banked_sample',
            attributes={'attribute1': 'value1'},
            to_one={'category': banked_sample_category}
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='banked_sample',
            attributes={'attribute1': 'value2'}
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual('sample', ret1.type)
        self.assertEqual(ret1.attributes, {
            'attribute1': 'value1',
            'banked_sample_category': 'category1'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual('sample', ret2.type)
        self.assertEqual(ret2.attributes, {
            'attribute1': 'value2'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
