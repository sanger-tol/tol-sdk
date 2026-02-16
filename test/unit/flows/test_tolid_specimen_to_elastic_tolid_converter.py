# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object,
)
from tol.core.data_object import DataObject
from tol.core.operator import Relational
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    TolidSpecimenToElasticTolidConverter
)


class _MockDataSourceTolid(DataSource, Relational):
    @property
    def supported_types(self):
        return ['specimen', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    def get_to_one_relation(self, source, relationship_name, session) -> DataObject | None:
        raise NotImplementedError()

    def get_to_many_relations(self, source, relationship_name, session) -> DataObject | None:
        raise NotImplementedError()

    @property
    def relationship_config(self) -> DataObject | None:
        return {'specimen': RelationshipConfig(to_one={'species': 'species'})}


class _MockDataSourceElastic(DataSource, Relational):
    @property
    def supported_types(self):
        return ['tolid', 'species', 'specimen']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    def get_to_one_relation(self, source, relationship_name, session) -> DataObject | None:
        raise NotImplementedError()

    def get_to_many_relations(self, source, relationship_name, session) -> DataObject | None:
        raise NotImplementedError()

    @property
    def relationship_config(self) -> DataObject | None:
        return {'tolid': RelationshipConfig(to_one={
            'species': 'species',
            'specimen': 'specimen'
        })}


class TestTolidSpecimenToElasticTolidConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceTolid(config={})
        destination = _MockDataSourceElastic(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TolidSpecimenToElasticTolidConverter(
            data_object_factory=destination.data_object_factory
        )

        mock_created_at = datetime.now()

        CoreDataObject = source.data_object_factory # noqa N806
        species1 = CoreDataObject(
            id_='123',
            type_='species',
            attributes={}
        )

        obj1 = CoreDataObject(
            id_='tolid_id1',
            type_='specimen',
            attributes={
                'specimen_id': 'specimen_id_1',
                'created_at': mock_created_at,
                'requested_taxonomy_id': 'requested_subspecies_1',
                'legacy_name': 'legacy_name_1',
            },
            to_one={
                'species': species1,
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual('tolid', ret1.type)
        self.assertEqual(ret1.attributes, {
            'created_at': mock_created_at,
            'requested_taxonomy_id': 'requested_subspecies_1',
            'legacy_name': 'legacy_name_1',
        })

        self.assertEqual(ret1.species.id, '123')
        self.assertEqual(ret1.species.type, 'species')
        self.assertEqual(ret1.specimen.id, 'specimen_id_1')
        self.assertEqual(ret1.specimen.type, 'specimen')
