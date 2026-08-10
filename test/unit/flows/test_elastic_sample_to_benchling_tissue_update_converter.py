# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import (
    RelationshipConfig
)
from tol.flows.converters import (
    ElasticSampleToBenchlingTissueUpdateConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['sample', 'sampleset', 'species', 'specimen', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'sampleset': 'sampleset',
            'species': 'species',
            'specimen': 'specimen',
            'tolid': 'tolid'
        }
        return {'sample': rc_sample}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.type == 'species':
            return source._host.data_object_factory(
                id_='species1',
                type_='species',
                attributes={
                    'taxon_group': 'order1',
                    'genome_size': 100
                }
            )
        if source.type == 'specimen':
            return source._host.data_object_factory(
                id_='specimen1',
                type_='specimen',
                attributes={
                    'taxon_group': 'order1',
                    'genome_size': 100
                }
            )
        if source.type == 'tolid':
            return source._host.data_object_factory(
                id_='tolid1',
                type_='specimen',
                attributes={
                    'taxon_group': 'order1',
                    'genome_size': 100
                }
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestElasticSampleToBenchlingTissueUpdateConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSampleToBenchlingTissueUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticSampleToBenchlingTissueUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        species = CoreDataObject(
            id_='species1',
            type_='species',
            attributes={
                'taxon_group': 'order1',
                'genome_size': 100,
                'scientific_name': 'scientific1',
                'family_representative': ['family1', 'family2']
            }
        )

        specimen = CoreDataObject(
            id_='specimen1',
            type_='specimen',
            attributes={
            }
        )
        tolid = CoreDataObject(
            id_='tolid1',
            type_='tolid',
            attributes={
            }
        )
        sampleset = CoreDataObject(
            id_='sampleset1',
            type_='sampleset',
            attributes={
            }
        )
        obj1 = CoreDataObject(
            id_='1234',
            type_='sample',
            attributes={
                'eln_tissue_id': 'benchling1',
                'rackid': 'rack1',
                'tubeid': 'tube1',
                'pos_in_rack': 'pos1',
                'location_parentage': 'parentage',
                'location_name': 'tray_name',
                'biosample_accession': 'biosample1',
                'calc_biospecimen_id': 'biospecimen1',
                'organism_part': ['part1', 'part2'],
                'lifestage': 'lifestage1',
                'sex': 'sex1',
                'tissue_size': 'size1',
                'hazard_group': 'level1',
                'preservation_approach': 'approach1',
                'receive_date': datetime(2022, 1, 1),
                'tollab_assign_date': datetime(2023, 1, 1),
                'send_rd': 'rd',
                'priority': '1',
                'project': 'project1',
                'sequencescape_study_id': 'cf01ea23-ac45-67e8-9101-11b213141516',
                'cost_code': 'S12345',
            },
            to_one={
                'species': species,
                'specimen': specimen,
                'tolid': tolid,
                'sampleset': sampleset
            }
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='sample',
            attributes={
                'eln_tissue_id': 'benchling1'
            }
        )

        converteds = converter.convert(obj1)

        id1, attributes1 = next(converteds)
        self.assertEqual('benchling1', id1)
        self.assertEqual(attributes1, {
            'rack_id': 'rack1',
            'tube_well_id': 'tube1',
            'tube_position': 'pos1',
            'scientific_name': 'scientific1',
            'taxon_id': 'species1',
            'taxon_group_phyla': 'order1',
            'genome_size': '100',
            'location': 'parentage',
            'tray': 'tray_name',
            'specimen_id': 'specimen1',
            'programme_id': 'tolid1',
            'biosample_id': 'biosample1',
            'biospecimen_id': 'biospecimen1',
            'organism_part': 'part1, part2',
            'lifestage': 'lifestage1',
            'sex': 'sex1',
            'preservation_approach': 'approach1',
            'hazard_group': 'level1',
            'size_of_tissue_in_tube': 'size1',
            'family_representative': 'family1, family2',
            'date_sample_received_at_sanger': '2022-01-01',
            'date_assigned_to_lab': '2023-01-01',
            'sample_set_id': 'sampleset1',
            'rd_sample': 'rd',
            'sts_id': 1234,
            'priority': '1',
            'project': 'project1',
            'study_id': 'cf01ea23-ac45-67e8-9101-11b213141516',
            'cost_code': 'S12345',
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        with self.assertRaises(StopIteration):
            next(converteds)
