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
    ElasticSampleToElasticSequencingRequestUpdateConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['specimen', 'sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'sts_specimen': 'specimen'
        }
        return {'sample': rc_sample}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
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


class TestElasticSampleToElasticSequencingRequestUpdateConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSampleToElasticSequencingRequestUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticSampleToElasticSequencingRequestUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        specimen = CoreDataObject(
            id_='specimen1',
            type_='specimen',
            attributes={}
        )
        obj1 = CoreDataObject(
            id_='sample1',
            type_='sample',
            attributes={},
            to_one={
                'sts_specimen': specimen
            }
        )

        converteds = converter.convert(obj1)
        id1, attributes1 = next(converteds)
        self.assertIsNone(id1)
        self.assertEqual(attributes1.get('mlwh_sample').id, 'sample1')
        self.assertEqual(attributes1.get('mlwh_specimen.id'), 'specimen1')

        with self.assertRaises(StopIteration):
            next(converteds)
