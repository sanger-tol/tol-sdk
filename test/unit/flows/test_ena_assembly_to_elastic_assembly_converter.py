# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
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
    EnaAssemblyToElasticAssemblyConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['assembly', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_assembly = RelationshipConfig()
        rc_assembly.to_one = {
            'species': 'species',
            'host_species': 'species'
        }
        return {'assembly': rc_assembly}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['assembly']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestEnaAssemblyToElasticAssemblyConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = EnaAssemblyToElasticAssemblyConverter(
            data_object_factory=destination.data_object_factory,
            config=EnaAssemblyToElasticAssemblyConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='Test1',
            type_='assembly',
            attributes={
                'strain': '123456',
                'tax_id': '123',
                'host_tax_id': '456',
                'another_attribute': ''
            }
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('Test1', ret1.id)
        self.assertEqual('assembly', ret1.type)
        self.assertEqual(ret1.attributes, {
            'strain': '123456',
        })
        self.assertEqual(ret1.to_one_relationships['species'].id, '123')
        self.assertEqual(ret1.to_one_relationships['host_species'].id, '456')

        with self.assertRaises(StopIteration):
            next(converteds)
