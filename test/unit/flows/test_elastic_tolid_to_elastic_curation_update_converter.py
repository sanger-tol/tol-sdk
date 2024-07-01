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
    ElasticTolidToElasticCurationUpdateConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['tolid', 'species']

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
        raise NotImplementedError()

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['curation']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestLabwhereLocationToElasticSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticTolidToElasticCurationUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='abCdeFghi1',
            type_='tolid',
            to_one={
                'tolid_species': CoreDataObject('species', '1234')
            }
        )

        obj2 = CoreDataObject(
            id_='cdEfgHilk1',
            type_='tolid',
            to_one={
                'tolid_species': CoreDataObject('species', '5678')
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'grit_tolid.id': 'abCdeFghi1',
            'species': {'id': '1234'},
        }))

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2, (None, {
            'grit_tolid.id': 'cdEfgHilk1',
            'species': {'id': '5678'},
        }))
