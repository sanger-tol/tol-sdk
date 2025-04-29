# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
# SPDX-License-Identifier: MIT

import datetime
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
    StsSampleProjectToElasticSampleConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sample_project', 'sample', 'project', 'sample_export_options',
                'location', 'gal', 'preservation_approach', 'sampleset',
                'specimen', 'preservative_solution', 'collection_method',
                'sample_person', 'person', 'manifest', 'tissue_size', 'sample_species',
                'species', 'lifestage', 'sex', 'organism_part', 'sample_species_organism_part',
                'ext_id', 'strain']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample_project = RelationshipConfig()
        rc_sample_project.to_one = {
            'sample': 'sample',
            'project': 'project'
        }
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'location': 'location',
            'gal': 'gal',
            'sampleset': 'sampleset',
            'manifest': 'manifest',
            'specimen': 'specimen',
            'preservation_approach': 'preservation_approach',
            'preservative_solution': 'preservative_solution',
            'collection_method': 'collection_method',
            'tissue_size': 'tissue_size',
            'sample_export_options': 'sample_export_options'
        }
        rc_sample.to_many = {
            'sample_persons': 'sample_person',
            'sample_species': 'sample_species',
            'ext_ids': 'ext_id'
        }
        rc_sample_person = RelationshipConfig()
        rc_sample_person.to_one = {
            'sample': 'sample',
            'person': 'person'
        }

        rc_sample_species = RelationshipConfig()
        rc_sample_species.to_one = {
            'sample': 'sample',
            'species': 'species',
            'lifestage': 'lifestage',
            'strain': 'strain',
            'sex': 'sex'
        }
        rc_sample_species.to_many = {
            'sample_species_organism_parts': 'sample_species_organism_part'
        }
        rc_sample_species_organism_part = RelationshipConfig()
        rc_sample_species_organism_part.to_one = {
            'organism_part': 'organism_part'
        }

        return {
            'sample_project': rc_sample_project,
            'sample': rc_sample,
            'sample_person': rc_sample_person,
            'sample_species': rc_sample_species,
            'sample_species_organism_part': rc_sample_species_organism_part
        }

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
        if relationship_name == 'sample_persons':
            person1 = source._host.data_object_factory(
                id_='test_person1',
                type_='person',
                attributes={
                    'fullname': 'full name1',
                }
            )
            person2 = source._host.data_object_factory(
                id_='test_person2',
                type_='person',
                attributes={
                    'fullname': 'full name2',
                }
            )
            sample_person1 = source._host.data_object_factory(
                id_='test_sample_person1',
                type_='sample_person',
                to_one={
                    'person': person1,
                },
                attributes={
                    'action': 'action1'
                }
            )
            sample_person2 = source._host.data_object_factory(
                id_='test_sample_person2',
                type_='sample_person',
                to_one={
                    'person': person2,
                },
                attributes={
                    'action': 'action2'
                }
            )
            return [sample_person1, sample_person2]
        elif relationship_name == 'sample_species':
            lifestage = source._host.data_object_factory(
                id_='test_lifestage',
                type_='lifestage',
                attributes={'name': 'EMBRYO'}
            )
            strain = source._host.data_object_factory(
                id_='test_strain',
                type_='strain',
                attributes={'name': 'Strain'}
            )
            sex = source._host.data_object_factory(
                id_='test_sex',
                type_='sex',
                attributes={
                    'name': 'FEMALE'
                }
            )
            sample = source._host.data_object_factory(
                id_='test_sample',
                type_='sample',
                attributes={}
            )
            species = source._host.data_object_factory(
                id_='test_species',
                type_='species',
                attributes={}
            )
            sample_species = source._host.data_object_factory(
                id_='test_sample_species',
                type_='sample_species',
                attributes={'target_or_symbiont': 'TARGET'},
                to_one={
                    'sample': sample,
                    'species': species,
                    'lifestage': lifestage,
                    'strain': strain,
                    'sex': sex
                }
            )
            sample_species_symbiont = source._host.data_object_factory(
                id_='test_sample_species_symbiont',
                type_='sample_species',
                attributes={'target_or_symbiont': 'SYMBIONT'},
                to_one={
                    'sample': sample,
                    'species': species,
                    'lifestage': lifestage,
                    'sex': sex
                }
            )
            return [sample_species, sample_species_symbiont]
        elif relationship_name == 'sample_species_organism_parts':
            op1 = source._host.data_object_factory(
                id_='test_op1',
                type_='organism_part',
                attributes={
                    'name': 'LEG'
                }
            )
            ssop1 = source._host.data_object_factory(
                id_='test_ssop1',
                type_='sample_species_organism_part',
                attributes={},
                to_one={
                    'organism_part': op1
                }
            )
            op2 = source._host.data_object_factory(
                id_='test_op2',
                type_='organism_part',
                attributes={
                    'name': 'HEAD'
                }
            )
            ssop2 = source._host.data_object_factory(
                id_='test_ssop2',
                type_='sample_species_organism_part',
                attributes={},
                to_one={
                    'organism_part': op2
                }
            )
            return [ssop1, ssop2]
        elif relationship_name == 'ext_ids':
            ext_id1 = source._host.data_object_factory(
                id_='ext_id1',
                type_='ext_id',
                attributes={
                    'ext_id_type': 'type1',
                    'value': 'ext_id1'
                }
            )
            ext_id2 = source._host.data_object_factory(
                id_='ext_id2',
                type_='ext_id',
                attributes={
                    'ext_id_type': 'type2',
                    'value': 'ext_id2'
                }
            )
            return [ext_id1, ext_id2]


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestStsSampleProjectToElasticSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsSampleProjectToElasticSampleConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        project = CoreDataObject(
            id_='test_project',
            type_='project',
            attributes={'programme': 'test_programme'}
        )
        location = CoreDataObject(
            id_='test_gal',
            type_='location',
            attributes={
                'location': 'Country | County | Town',
                'lat': 12.345678,
                'long': 23.456789,
                'elevation': 65,
                'depth': 200,
                'habitat': 'Woodland'
            }
        )
        gal = CoreDataObject(
            id_='test_gal',
            type_='gal',
            attributes={
                'name': 'Test Gal',
                'abbreviation': 'TESTGAL'
            }
        )
        specimen = CoreDataObject(
            id_='test_specimen',
            type_='specimen',
            attributes={}
        )
        sampleset = CoreDataObject(
            id_='test_sampleset',
            type_='sampleset',
            attributes={}
        )
        manifest = CoreDataObject(
            id_='test_manifest',
            type_='manifest',
            attributes={}
        )
        tissue_size = CoreDataObject(
            id_='test_tissue_size',
            type_='tissue_size',
            attributes={
                'size': 'huge'
            }
        )
        sample_export_options = CoreDataObject(
            id_='test_sample_export_options',
            type_='sample_export_options',
            attributes={
                'display_name': 'labwork1'
            }
        )
        approach = CoreDataObject(
            id_='test_approach',
            type_='preservation_approach',
            attributes={
                'approach': 'approach'
            }
        )
        solution = CoreDataObject(
            id_='test_solution',
            type_='preservative_solution',
            attributes={
                'solution': 'solution'
            }
        )
        method = CoreDataObject(
            id_='test_method',
            type_='collection_method',
            attributes={
                'method': 'method_desc'
            }
        )
        sample = CoreDataObject(
            id_='test_sample',
            type_='sample',
            attributes={
                'col_date': '2020-02-02',
                'original_collection_date': '2011-01-01 12:00:00',
                'pre_date': '2000-12-12',
                'public_name': 'xxTesTest1',
                'other': 'another',
                'sequencescape_study_id': 'cf01ea23-ac45-67e8-9101-11b213141516',
                'cost_code': 'S12345',
            },
            to_one={
                'location': location,
                'gal': gal,
                'preservation_approach': approach,
                'preservative_solution': solution,
                'collection_method': method,
                'specimen': specimen,
                'sampleset': sampleset,
                'manifest': manifest,
                'tissue_size': tissue_size,
                'sample_export_options': sample_export_options
            }
        )
        sample_project = CoreDataObject(
            id_='test_sample_project',
            type_='sample_project',
            attributes={},
            to_one={
                'sample': sample,
                'project': project
            }
        )
        converteds = converter.convert(sample_project)
        ret1 = next(converteds)
        self.assertEqual('test_sample', ret1.id)
        self.assertEqual('sample', ret1.type)
        self.maxDiff = None
        self.assertEqual(ret1.attributes, {
            'project': ['test_project'],
            'programme': ['test_programme'],
            'collection_country': 'Country',
            'collection_locality': 'County | Town',
            'latitude': 12.345678,
            'longitude': 23.456789,
            'elevation': 65,
            'depth': 200,
            'habitat': 'Woodland',
            'gal_abbreviation': 'TESTGAL',
            'gal_name': 'Test Gal',
            'preservation_approach': 'approach',
            'preservative_solution': 'solution',
            'collection_method_desc': 'method_desc',
            'specimen': {'id': 'test_specimen'},
            'sampleset': {'id': 'test_sampleset'},
            'manifest': {'id': 'test_manifest'},
            'tissue_size': 'huge',
            'lab_work_category': 'labwork1',
            'col_date': datetime.datetime(2020, 2, 2),
            'original_collection_date': datetime.datetime(2011, 1, 1, 12),
            'pre_date': datetime.datetime(2000, 12, 12),
            'tolid': {'id': 'xxTesTest1'},
            'public_name': None,
            'other': 'another',
            'action1_name': 'full name1',
            'action2_name': 'full name2',
            'sequencescape_study_id': 'cf01ea23-ac45-67e8-9101-11b213141516',
            'cost_code': 'S12345',
            'species': {'id': 'test_species'},
            'lifestage': 'EMBRYO',
            'strain': 'Strain',
            'type1': 'ext_id1',
            'type2': 'ext_id2',
            'sex': 'FEMALE',
            'organism_part': ['LEG', 'HEAD']
        })

        with self.assertRaises(StopIteration):
            next(converteds)
