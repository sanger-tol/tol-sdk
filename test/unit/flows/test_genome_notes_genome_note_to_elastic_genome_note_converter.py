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
    GenomeNotesGenomeNoteToElasticGenomeNoteConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['assembly', 'genome_note', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_genome_note = RelationshipConfig()
        rc_genome_note.to_one = {
            'assembly': 'assembly',
            'tolid': 'tolid'
        }
        return {'genome_note': rc_genome_note}

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
        return ['genome_note']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestGenomeNotesGenomeNoteToElasticGenomeNoteConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = GenomeNotesGenomeNoteToElasticGenomeNoteConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='Test1',
            type_='genome_note',
            attributes={
                'passed_pr': True,
                'assembly_accession': 'assembly1',
                'tolid': 'tolid1',
                'another_attribute': 'another_value'
            }
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('Test1', ret1.id)
        self.assertEqual('genome_note', ret1.type)
        self.assertEqual(ret1.attributes, {
            'passed_pr': True,
            'another_attribute': 'another_value'
        })
        self.assertEqual(ret1.to_one_relationships['assembly'].id, 'assembly1')
        self.assertEqual(ret1.to_one_relationships['tolid'].id, 'tolid1')

        with self.assertRaises(StopIteration):
            next(converteds)
