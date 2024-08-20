# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
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
        return ['sample', 'species', 'specimen', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'sts_species': 'species',
            'sts_specimen': 'specimen',
            'sts_tolid': 'tolid'
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
                    'sts_taxon_group': 'order1',
                    'sts_genome_size': 100
                }
            )
        if source.type == 'specimen':
            return source._host.data_object_factory(
                id_='specimen1',
                type_='specimen',
                attributes={
                    'sts_taxon_group': 'order1',
                    'sts_genome_size': 100
                }
            )
        if source.type == 'tolid':
            return source._host.data_object_factory(
                id_='tolid1',
                type_='specimen',
                attributes={
                    'sts_taxon_group': 'order1',
                    'sts_genome_size': 100
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
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        species = CoreDataObject(
            id_='species1',
            type_='species',
            attributes={
                'sts_taxon_group': 'order1',
                'sts_genome_size': 100,
                'sts_scientific_name': 'scientific1',
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
        obj1 = CoreDataObject(
            id_='1234',
            type_='sample',
            attributes={
                'benchling_eln_tissue_id': 'benchling1',
                'sts_rackid': 'rack1',
                'sts_tubeid': 'tube1',
                'sts_pos_in_rack': 'pos1',
                'sts_labwhere_parentage': 'parentage',
                'sts_labwhere_name': 'tray_name',
                'sts_biosample_accession': 'biosample1',
                'sts_receive_date': datetime(2022, 1, 1),
                'sts_tollab_assign_date': datetime(2023, 1, 1),
                'sts_sampleset_id': 'sampleset1',
                'sts_send_rd': 'rd',
                'sts_priority': '1',
                'sts_project': ['project1', 'project2']
            },
            to_one={
                'sts_species': species,
                'sts_specimen': specimen,
                'sts_tolid': tolid
            }
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='sample',
            attributes={
                'benchling_eln_tissue_id': 'benchling1'
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
            'freezer': None,
            'shelf': 'parentage',
            'tray': 'tray_name',
            'specimen_id': 'specimen1',
            'programme_id': 'tolid1',
            'biosample_id': 'biosample1',
            'date_sample_received_at_sanger': '2022-01-01',
            'date_assigned_to_lab': '2023-01-01',
            'sample_set_id': 'sampleset1',
            'rd_sample': 'rd',
            'sts_id': 1234,
            'priority': '1',
            'project': 'project1, project2',
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        with self.assertRaises(StopIteration):
            next(converteds)
