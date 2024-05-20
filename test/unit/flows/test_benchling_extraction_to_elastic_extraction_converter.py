# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BenchlingExtractionToElasticExtractionConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['extraction']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBenchlingExtractionToElasticExtractionConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BenchlingExtractionToElasticExtractionConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='extraction_id1',
            type_='extraction',
            attributes={
                'sts_id': 'sts_id_1',
                'taxon_id': 'taxon_id_1',
                'eln_tissue_prep_id': 'tissue_prep_id_1',
                'programme_id': 'programme_id_1',
                'specimen_id': 'specimen_id_1',
                'eln_tissue_prep_name': 'tissue_prep_name1',
            }
        )

        obj2 = CoreDataObject(
            id_='extraction_id2',
            type_='extraction',
            attributes={
                'sts_id': 'sts_id_2',
                'taxon_id': 'taxon_id_2',
                'eln_tissue_prep_id': 'tissue_prep_id_2',
                'eln_tissue_prep_name': 'tissue_prep_name2',
                'specimen_id': 'specimen_id_2',
                'weight_mg': 24,
                'dowstream_protocol': 'Plant MagAttract v4'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'sample': {'id': 'sts_id_1'},
            'species': {'id': 'taxon_id_1'},
            'specimen': {'id': 'specimen_id_1'},
            'tolid': {'id': 'programme_id_1'},
            'tissue_prep': {'id': 'tissue_prep_id_1'},
            'eln_tissue_prep_name': 'tissue_prep_name1'
        })

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'sample': {'id': 'sts_id_2'},
            'species': {'id': 'taxon_id_2'},
            'specimen': {'id': 'specimen_id_2'},
            'tolid': {'id': None},
            'tissue_prep': {'id': 'tissue_prep_id_2'},
            'eln_tissue_prep_name': 'tissue_prep_name2',
            'weight_mg': 24,
            'dowstream_protocol': 'Plant MagAttract v4'
        })
