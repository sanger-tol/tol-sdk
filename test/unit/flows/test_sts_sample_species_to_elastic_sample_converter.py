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
    StsSampleSpeciesToElasticSampleConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sample_species', 'sample', 'species',
                'lifestage', 'sex', 'organism_part',
                'sample_species_organism_part']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample_species = RelationshipConfig()
        rc_sample_species.to_one = {
            'sample': 'sample',
            'species': 'species',
            'lifestage': 'lifestage',
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
        print('HERE', flush=True)
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


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestStsSampleSpeciesToElasticSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsSampleSpeciesToElasticSampleConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        lifestage = CoreDataObject(
            id_='test_lifestage',
            type_='lifestage',
            attributes={'name': 'EMBRYO'}
        )
        sex = CoreDataObject(
            id_='test_sex',
            type_='sex',
            attributes={
                'name': 'FEMALE'
            }
        )
        sample = CoreDataObject(
            id_='test_sample',
            type_='sample',
            attributes={}
        )
        species = CoreDataObject(
            id_='test_species',
            type_='species',
            attributes={}
        )
        sample_species = CoreDataObject(
            id_='test_sample_species',
            type_='sample_species',
            attributes={},
            to_one={
                'sample': sample,
                'species': species,
                'lifestage': lifestage,
                'sex': sex
            }
        )
        converteds = converter.convert(sample_species)
        ret1 = next(converteds)
        self.assertEqual('test_sample', ret1.id)
        self.assertEqual('sample', ret1.type)
        self.assertEqual(ret1.attributes, {
            'species': {'id': 'test_species'},
            'lifestage': 'EMBRYO',
            'sex': 'FEMALE',
            'organism_part': ['LEG', 'HEAD']
        })

        with self.assertRaises(StopIteration):
            next(converteds)
