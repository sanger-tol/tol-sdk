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
from tol.core.relationship import (
    RelationshipConfig
)
from tol.flows.converters import (
    ElasticTolidToElasticGenomeNoteUpdateConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['species', 'tolid', 'genome_note']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_tolid = RelationshipConfig()
        rc_tolid.to_one = {
            'tolid_species': 'species'
        }
        return {'tolid': rc_tolid}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.type == 'tolid':
            return source._host.data_object_factory(
                id_='species1',
                type_='species',
                attributes={}
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestElasticTolidToElasticGenomeNoteUpdateConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticTolidToElasticGenomeNoteUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        species = CoreDataObject(
            id_='species1',
            type_='species',
            attributes={}
        )
        obj1 = CoreDataObject(
            id_='tolid1',
            type_='tolid',
            attributes={},
            to_one={
                'tolid_species': species
            }
        )

        converteds = converter.convert(obj1)
        id1, attributes1 = next(converteds)
        self.assertIsNone(id1)
        print(attributes1)
        assert attributes1['gn_tolid.id'] == 'tolid1'
        assert attributes1['gn_species'] == {'id': 'species1'}

        with self.assertRaises(StopIteration):
            next(converteds)
