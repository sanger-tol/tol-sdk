# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

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
    ElasticSampleToBenchlingSampleConverter
)


class _MockDataSource(DataSource, Relational):
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
        return source.to_one.get(relationship_name)

    def get_to_many_relations(
            self
    ):
        raise NotImplementedError()


class TestElasticSampleToBenchlingSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSampleToBenchlingSampleConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='sample_id1',
            type_='sample',
            attributes={
                'benchling_eln_tissue_id': 'benchling1',
                'benchling_another': 'another1',
                'benchling_another2': None
            },
            to_one={
                'benchling_species': CoreDataObject('species', 'taxon_id_1'),
                'benchling_specimen': CoreDataObject('specimen', 'specimen_id_1'),
                'benchling_tolid': CoreDataObject('tolid', 'programme_id_1')
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)

        self.assertEqual('benchling1', ret1.id)
        self.assertEqual('sample', ret1.type)
        self.assertEqual(ret1.attributes, {
            'another': 'another1',
            'another2': None,
            'taxon_id': 'taxon_id_1',
            'specimen_id': 'specimen_id_1',
            'programme_id': 'programme_id_1',
            'sts_id': 'sample_id1'
        })
