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
    MlwhRunDataToElasticRunDataConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['run_data', 'species', 'specimen', 'sequencing_request', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_run_data = RelationshipConfig()
        rc_run_data.to_one = {
            'species': 'species',
            'specimen': 'specimen',
            'sequencing_request': 'sequencing_request',
            'tolid': 'tolid'
        }
        return {'run_data': rc_run_data}

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
        return ['run_data']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestMlwhRunDataToElasticRunDataConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = MlwhRunDataToElasticRunDataConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='Test1',
            type_='run_data',
            attributes={
                'taxon_id': '1234',
                'supplier_name': 'supplier1',
                'sample_ref': 'sample1',
                'tolid': 'tolid1',
                'attribute1': 'value1'
            }
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('Test1', ret1.id)
        self.assertEqual('run_data', ret1.type)
        self.assertEqual(ret1.attributes, {
            'attribute1': 'value1'
        })
        self.assertEqual(ret1.to_one_relationships['species'].id, '1234')
        self.assertEqual(ret1.to_one_relationships['specimen'].id, 'supplier1')
        self.assertEqual(ret1.to_one_relationships['sequencing_request'].id, 'sample1')
        self.assertEqual(ret1.to_one_relationships['tolid'].id, 'tolid1')

        with self.assertRaises(StopIteration):
            next(converteds)
