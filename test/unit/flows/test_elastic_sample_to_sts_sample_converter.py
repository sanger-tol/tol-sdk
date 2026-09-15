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
    ElasticSampleToStsSampleConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['sample', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'tolid': 'tolid',
        }
        return {'sample': rc_sample}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.type == 'tolid':
            return source._host.data_object_factory(
                id_='tolid1',
                type_='tolid',
                attributes={}
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestElasticSampleToStsSampleConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSampleToStsSampleConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticSampleToStsSampleConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        tolid = CoreDataObject(
            id_='tolid1',
            type_='tolid',
            attributes={}
        )

        obj1 = CoreDataObject(
            id_='1234',
            type_='sample',
            attributes={
                'eln_tissue_id': 'tissue_id',
            },
            to_one={
                'tolid': tolid
            }
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='sample',
            attributes={
                'eln_tissue_id': 'tissue_id2',
                'eln_updated_at': datetime(2020, 1, 1),
                'ep_exported': True
            }
        )

        obj3 = CoreDataObject(
            id_='test3',
            type_='sample',
            attributes={
                'eln_updated_at': None,
                'ep_exported': False
            }
        )

        converteds = converter.convert(obj1)
        dt = datetime.now()
        ret1 = next(converteds)
        self.assertEqual('1234', ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual('tolid1', ret1.attributes['public_name'])
        self.assertEqual('tissue_id', ret1.attributes['eln_id'])
        self.assertTrue(ret1.attributes['ep_exported'])
        self.assertTrue(
            ret1.attributes['eln_updated_at'] >= dt
        )

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret1 = next(converteds)
        self.assertEqual('test2', ret1.id)
        self.assertEqual(obj2.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'public_name': None,
            'eln_id': 'tissue_id2',
            'eln_updated_at': datetime(2020, 1, 1),
            'ep_exported': True
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj3)
        ret3 = next(converteds)
        self.assertEqual('test3', ret3.id)
        self.assertEqual(obj3.type, ret3.type)
        self.assertEqual(ret3.attributes, {
            'public_name': None,
            'eln_id': None,
            'eln_updated_at': None,
            'ep_exported': False
        })

        with self.assertRaises(StopIteration):
            next(converteds)
