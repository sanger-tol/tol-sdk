# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import Relational
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    TolqcSpeciesToElasticSpeciesConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['species', 'accession']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_species = RelationshipConfig()
        rc_species.to_one = {
            'data_accession': 'accession',
            'umbrella_accession': 'accession',
        }
        return {'species': rc_species}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.id == 'Abax parallelepipedus' and relationship_name == 'data_accession':
            return source._host.data_object_factory(
                id_='accession_id1',
                type_='accession',
            )
        if source.id == 'Abax parallelepipedus' and relationship_name == 'umbrella_accession':
            return source._host.data_object_factory(
                id_='accession_id2',
                type_='accession',
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockElasticDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestTolqcSpeciesToElasticSpeciesConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockElasticDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TolqcSpeciesToElasticSpeciesConverter(
            data_object_factory=destination.data_object_factory,
            config=TolqcSpeciesToElasticSpeciesConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='Abax parallelepipedus',
            type_='species',
            attributes={
                'chromosome_number': '35',
                'taxon_family': 'Carabidae',
                'taxon_group': 'insects',
                'taxon_id': '102642',
                'taxon_order': 'Coleoptera',
                'taxon_phylum': 'Arthropoda'
            }
        )
        obj2 = CoreDataObject(
            id_='Abdera quadrifasciata',
            type_='species',
            attributes={
                'chromosome_number': '20',
                'taxon_family': 'Melandryidae',
                'taxon_group': 'insects',
                'taxon_id': '433183',
                'taxon_order': 'Coleoptera',
                'taxon_phylum': 'Arthropoda'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.attributes['taxon_id'], ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'chromosome_number': '35',
            'family': 'Carabidae',
            'group': 'insects',
            'order_group': 'Coleoptera',
            'taxon_group': 'Arthropoda',
            'scientific_name': 'Abax parallelepipedus',
            'bioproject_accession': 'accession_id1',
            'umbrella_bioproject_accession': 'accession_id2'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.attributes['taxon_id'], ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'chromosome_number': '20',
            'family': 'Melandryidae',
            'group': 'insects',
            'order_group': 'Coleoptera',
            'taxon_group': 'Arthropoda',
            'scientific_name': 'Abdera quadrifasciata'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
