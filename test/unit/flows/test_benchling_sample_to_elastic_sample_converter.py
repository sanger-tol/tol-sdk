# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
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
    BenchlingSampleToElasticSampleConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return [
            'sample', 'species', 'specimen', 'tolid'
        ]

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'species': 'species',
            'specimen': 'specimen',
            'tolid': 'tolid',
        }
        return {'sample': rc_sample}

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


class TestBenchlingSampleToElasticSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BenchlingSampleToElasticSampleConverter(
            data_object_factory=destination.data_object_factory,
            config=BenchlingSampleToElasticSampleConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='sample_id_1',
            type_='sample',
            attributes={
                'taxon_id': 'taxon_id_1',
                'specimen_id': 'specimen_id_1',
                'programme_id': 'programme_id_1',
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {})
        self.assertEqual(ret1.species.id, 'taxon_id_1')
        self.assertEqual(ret1.specimen.id, 'specimen_id_1')
        self.assertEqual(ret1.tolid.id, 'programme_id_1')

        obj2 = CoreDataObject(
            id_=None,
            type_='sample',
            attributes={
                'taxon_id': 'taxon_id_1',
                'specimen_id': 'specimen_id_1',
                'programme_id': 'programme_id_1',
            }
        )
        converteds = converter.convert(obj2)
        with self.assertRaises(StopIteration):
            next(converteds)
