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
    ElasticSampleToElasticExtractionContainerUpdateConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sample', 'sampleset']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'sts_sampleset': 'sampleset'
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


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['extraction_container']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestElasticSampleToElasticExtractionContainerUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSampleToElasticExtractionContainerUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticSampleToElasticExtractionContainerUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='1234',
            type_='sample',
            to_one={
                'sts_sampleset': CoreDataObject('sampleset', '5678')
            }
        )

        obj2 = CoreDataObject(
            id_='2345',
            type_='sample',
            to_one={
                'sts_sampleset': CoreDataObject('sampleset', '6789')
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'benchling_sample.id': '1234',
            'sampleset': {'id': '5678'},
        }))

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2, (None, {
            'benchling_sample.id': '2345',
            'sampleset': {'id': '6789'},
        }))
