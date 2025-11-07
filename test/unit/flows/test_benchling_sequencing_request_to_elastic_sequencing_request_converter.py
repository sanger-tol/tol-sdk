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
    BenchlingSequencingRequestToElasticSequencingRequestConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sequencing_request']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return [
            'sequencing_request', 'extraction', 'sample', 'species', 'specimen', 'tolid',
            'tissue_prep'
        ]

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sequencing_request = RelationshipConfig()
        rc_sequencing_request.to_one = {
            'sample': 'sample',
            'species': 'species',
            'specimen': 'specimen',
            'tolid': 'tolid',
            'tissue_prep': 'tissue_prep',
            'extraction': 'extraction'
        }
        return {'sequencing_request': rc_sequencing_request}

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


class TestBenchlingSequencingRequestToElasticSequencingRequestConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BenchlingSequencingRequestToElasticSequencingRequestConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='sequencing_request_id_1',
            type_='sequencing_request',
            attributes={
                'sanger_sample_id': 'sanger_sample_id_1',
                'sts_id': 'sts_id_1',
                'taxon_id': 'taxon_id_1',
                'specimen_id': 'specimen_id_1',
                'tissue_prep_id': 'tissue_prep_id_1',
                'programme_id': 'programme_id_1',
                'extraction_id': 'extraction_id_1',
                'sequencing_platform': 'pacbio',
                'source': 'v1'
            }
        )

        obj2 = CoreDataObject(
            id_='sequencing_request_id_2',
            type_='sequencing_request',
            attributes={
                'sanger_sample_id': 'sanger_sample_id_2',
                'sts_id': 'sts_id_2',
                'taxon_id': 'taxon_id_2',
                'specimen_id': 'specimen_id_2',
                'programme_id': 'programme_id_2',
                'sequencing_platform': 'pacbio',
                'source': 'v1'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.attributes['sanger_sample_id'], ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'sequencing_platform': 'pacbio',
            'source': 'v1'
        })
        self.assertEqual(ret1.sample.id, 'sts_id_1')
        self.assertEqual(ret1.species.id, 'taxon_id_1')
        self.assertEqual(ret1.specimen.id, 'specimen_id_1')
        self.assertEqual(ret1.tolid.id, 'programme_id_1')
        self.assertEqual(ret1.tissue_prep.id, 'tissue_prep_id_1')
        self.assertEqual(ret1.extraction.id, 'extraction_id_1')

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.attributes['sanger_sample_id'], ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'sequencing_platform': 'pacbio',
            'source': 'v1'
        })
        self.assertEqual(ret2.sample.id, 'sts_id_2')
        self.assertEqual(ret2.species.id, 'taxon_id_2')
        self.assertEqual(ret2.specimen.id, 'specimen_id_2')
        self.assertEqual(ret2.tolid.id, 'programme_id_2')
        self.assertTrue(ret2.tissue_prep is None)
        self.assertTrue(ret2.extraction is None)
