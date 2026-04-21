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
    GapAssemblyToElasticAssemblyConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['assembly', 'assembly_detail', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_assembly = RelationshipConfig()
        rc_assembly.to_one = {
            'species': 'species'
        }
        rc_assembly.to_many = {
            'assembly_details': 'assembly_detail'
        }
        return {'assembly': rc_assembly}

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
        return [
            source._host.data_object_factory(
                'assembly_detail',
                'Contig N50',
                attributes={
                    'info': '12345'
                }
            ),
            source._host.data_object_factory(
                'assembly_detail',
                'Scaffold N50',
                attributes={
                    'info': '23456'
                }
            )
        ]


class _MockDataSourceDestination(DataSource, Relational):

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
            'species': 'species'
        }
        return {'assembly': rc_assembly}

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
        pass


class TestGapAssemblyToElasticAssemblyConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSourceDestination(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = GapAssemblyToElasticAssemblyConverter(
            data_object_factory=destination.data_object_factory,
            config=GapAssemblyToElasticAssemblyConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='Test1',
            type_='assembly',
            attributes={
                'project': 'Lepidoptera',
                'assembly_name': 'ASM270686v2',
                'lustre_path_assembly': '/some/path',
                'taxon_id': 123,
            }
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('Test1', ret1.id)
        self.assertEqual('assembly', ret1.type)
        self.assertEqual(ret1.attributes, {
            'project': 'Lepidoptera',
            'assembly_name': 'ASM270686v2',
            'lustre_path_assembly': '/some/path',
            'contig_n50': '12345',
            'scaffold_n50': '23456',
        })

        self.assertEqual(ret1.to_one_relationships['species'].id, '123')

        with self.assertRaises(StopIteration):
            next(converteds)
