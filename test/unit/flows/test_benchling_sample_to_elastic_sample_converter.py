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
    BenchlingSampleToElasticSampleConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceDestination(DataSource, Relational):
    @property
    def supported_types(self):
        return ['sample', 'species', 'specimen', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'benchling_species': 'species',
            'benchling_specimen': 'specimen',
            'benchling_tolid': 'tolid'
        }
        return {'sample': rc_sample}

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


class TestBenchlingSampleToElasticSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceDestination(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BenchlingSampleToElasticSampleConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='sample_id1',
            type_='sample',
            attributes={'sts_id': 'sts_id_1',
                        'taxon_id': 'taxon_id_1',
                        'programme_id': 'programme_id_1',
                        'specimen_id': 'specimen_id_1',
                        'another': 'another1',
                        'another2': None
                        }
        )

        obj2 = CoreDataObject(
            id_='sample_id2',
            type_='sample',
            attributes={'sts_id': 'sts_id_2',
                        'taxon_id': 'taxon_id_2',
                        'programme_id': None,
                        'specimen_id': 'specimen_id_2',
                        'another': 'another2',
                        'another2': 'another22'}
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.attributes['sts_id'], ret1.id)
        self.assertEqual('sample', ret1.type)
        self.assertEqual(ret1.attributes, {
            'benchling_another': 'another1',
            'benchling_another2': None
        })
        self.assertEqual(ret1.benchling_specimen.id, 'specimen_id_1')
        self.assertEqual(ret1.benchling_species.id, 'taxon_id_1')
        self.assertEqual(ret1.benchling_tolid.id, 'programme_id_1')

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.attributes['sts_id'], ret2.id)
        self.assertEqual('sample', ret2.type)
        self.assertEqual(ret2.attributes, {
            'benchling_another': 'another2',
            'benchling_another2': 'another22'
        })
        self.assertEqual(ret2.benchling_specimen.id, 'specimen_id_2')
        self.assertEqual(ret2.benchling_species.id, 'taxon_id_2')
        self.assertIsNone(ret2.benchling_tolid)
