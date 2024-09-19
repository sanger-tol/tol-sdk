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
    ElasticTolidToElasticSampleUpdateConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['tolid', 'species', 'specimen', 'sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_tolid = RelationshipConfig()
        rc_tolid.to_one = {
            'tolid_species': 'species',
            'tolid_specimen': 'specimen'
        }
        return {'tolid': rc_tolid}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.type == 'species':
            return source._host.data_object_factory(
                id_='species1',
                type_='species',
                attributes={}
            )
        if source.type == 'specimen':
            return source._host.data_object_factory(
                id_='specimen1',
                type_='specimen',
                attributes={}
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestElasticTolidToElasticSampleUpdateConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticTolidToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        species = CoreDataObject(
            id_='species1',
            type_='species',
            attributes={}
        )

        specimen = CoreDataObject(
            id_='specimen1',
            type_='specimen',
            attributes={}
        )
        obj1 = CoreDataObject(
            id_='tolid1',
            type_='tolid',
            attributes={},
            to_one={
                'tolid_species': species,
                'tolid_specimen': specimen
            }
        )
        obj2 = CoreDataObject(
            id_='tolid2',
            type_='tolid',
            attributes={}
        )

        converteds = converter.convert(obj1)
        id1, attributes1 = next(converteds)
        self.assertIsNone(id1)
        self.assertEqual(attributes1, {
            'tolid_tolid': {'id': 'tolid1'},
            'sts_species.id': 'species1',
            'sts_specimen.id': 'specimen1',
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        with self.assertRaises(StopIteration):
            next(converteds)
