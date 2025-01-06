# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
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


class TestBenchlingSequencingRequestToElasticSequencingRequestConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
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
            'sample': {'id': 'sts_id_1'},
            'species': {'id': 'taxon_id_1'},
            'specimen': {'id': 'specimen_id_1'},
            'tolid': {'id': 'programme_id_1'},
            'extraction': {'id': 'extraction_id_1'},
            'tissue_prep': {'id': 'tissue_prep_id_1'},
            'sequencing_platform': 'pacbio',
            'source': 'v1'
        })

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.attributes['sanger_sample_id'], ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'sample': {'id': 'sts_id_2'},
            'species': {'id': 'taxon_id_2'},
            'specimen': {'id': 'specimen_id_2'},
            'tolid': {'id': 'programme_id_2'},
            'extraction': None,
            'tissue_prep': None,
            'sequencing_platform': 'pacbio',
            'source': 'v1'
        })
