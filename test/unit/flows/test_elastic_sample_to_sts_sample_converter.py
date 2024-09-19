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
            'tolid_tolid': 'tolid',
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
            data_object_factory=destination.data_object_factory
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
                'benchling_eln_tissue_id': 'tissue_id'
            },
            to_one={
                'tolid_tolid': tolid
            }
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='sample',
            attributes={
                'benchling_eln_tissue_id': 'tissue_id2'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('1234', ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'public_name': 'tolid1',
            'eln_id': 'tissue_id'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret1 = next(converteds)
        self.assertEqual('test2', ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'public_name': None,
            'eln_id': 'tissue_id2'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
