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
    GapAssemblyToElasticAssemblyAnalysisConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['assembly', 'pipeline', 'species']

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
            'pipelines': 'pipeline'
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
                'pipeline',
                'sequencecomposition',
                attributes={
                    'analysis': 'Sequence Composition',
                    'results': 'Base Content',
                    's3': 's3://bucket/path/to/file',
                    'lustre_path_analysis': '/some/path',
                }
            ),
            source._host.data_object_factory(
                'pipeline',
                'blobtoolkit',
                attributes={
                    'analysis': 'BlobToolKit',
                    'results': 'BlobToolKit',
                    's3': 's3://bucket/path/to/file2',
                    'lustre_path_analysis': '/some/path2',
                }
            )
        ]


class _MockDataSourceDestination(DataSource, Relational):

    @property
    def supported_types(self):
        return ['assembly', 'assembly_analysis', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_assembly_analysis = RelationshipConfig()
        rc_assembly_analysis.to_one = {
            'assembly': 'assembly',
            'species': 'species'
        }
        return {'assembly_analysis': rc_assembly_analysis}

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


class TestGapAssemblyToElasticAssemblyAnalysisConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSourceDestination(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = GapAssemblyToElasticAssemblyAnalysisConverter(
            data_object_factory=destination.data_object_factory
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
        self.assertEqual('Test1_sequencecomposition', ret1.id)
        self.assertEqual('assembly_analysis', ret1.type)
        self.assertEqual(ret1.attributes, {
            'analysis': 'Sequence Composition',
            'results': 'Base Content',
            's3': 's3://bucket/path/to/file',
            'lustre_path_analysis': '/some/path',
        })

        self.assertEqual(ret1.to_one_relationships['assembly'].id, 'Test1')
        self.assertEqual(ret1.to_one_relationships['species'].id, '123')

        ret2 = next(converteds)
        self.assertEqual('Test1_blobtoolkit', ret2.id)
        self.assertEqual('assembly_analysis', ret2.type)
        self.assertEqual(ret2.attributes, {
            'analysis': 'BlobToolKit',
            'results': 'BlobToolKit',
            's3': 's3://bucket/path/to/file2',
            'lustre_path_analysis': '/some/path2',
        })

        self.assertEqual(ret2.to_one_relationships['assembly'].id, 'Test1')
        self.assertEqual(ret2.to_one_relationships['species'].id, '123')

        with self.assertRaises(StopIteration):
            next(converteds)
