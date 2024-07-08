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
    TolidToElasticConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['tolid', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    def get_to_one_relation(self, source, relationship_name, session) -> DataObject | None:
        raise NotImplementedError()

    def get_to_many_relations(self, source, relationship_name, session) -> DataObject | None:
        raise NotImplementedError()

    @property
    def relationship_config(self) -> DataObject | None:
        return {'tolid': RelationshipConfig(to_one={'species': 'species'})}


class TestBenchlingExtractionToElasticExtractionConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TolidToElasticConverter(
            data_object_factory=destination.data_object_factory
        )

        mock_created_at = datetime.now()

        CoreDataObject = source.data_object_factory # noqa N806
        species1 = CoreDataObject(
            id_='123',
            type_='species',
            attributes={
                'name': 'species_name1',
                'requested_tolid': 'requested_tolid_1',
            }
        )

        obj1 = CoreDataObject(
            id_='tolid_id1',
            type_='tolid',
            attributes={
                'specimen_id': 'specimen_id_1',
                'created_at': mock_created_at
            },
            to_one={
                'species': species1,
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'specimen_id': 'specimen_id_1',
            'created_at': mock_created_at,
        })

        self.assertEqual(ret1.species.id, '123')
        self.assertEqual(ret1.species.type, 'species')
        self.assertEqual(ret1.species.attributes, {
            'tolid_name': 'species_name1',
            'requested_tolid': 'requested_tolid_1'
        })
