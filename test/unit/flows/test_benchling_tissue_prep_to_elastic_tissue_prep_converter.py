# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BenchlingTissuePrepToElasticTissuePrepConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['tissue_prep']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBenchlingTissuePrepToElasticTissuePrepConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BenchlingTissuePrepToElasticTissuePrepConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='tissue_prep_id1',
            type_='tissue_prep',
            attributes={'sts_id': 'sts_id_1',
                        'taxon_id': 'taxon_id_1',
                        'eln_tissue_prep_id': 'tissue_prep_id1',
                        'programme_id': 'programme_id_1',
                        'eln_tissue_prep_name': 'tissue_prep_name1',
                        'weight_mg': 12,
                        'tissue_prep_type': None
                        }
        )

        obj2 = CoreDataObject(
            id_='tissue_prep_id2',
            type_='tissue_prep',
            attributes={'sts_id': 'sts_id_2',
                        'taxon_id': 'taxon_id_2',
                        'eln_tissue_prep_id': 'tissue_prep_id2',
                        'eln_tissue_prep_name': 'tissue_prep_name2',
                        'weight_mg': 24,
                        'dowstream_protocol': 'Plant MagAttract v4'
                        }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.attributes['eln_tissue_prep_id'], ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'sample': {'id': 'sts_id_1'},
            'species': {'id': 'taxon_id_1'},
            'tolid': {'id': 'programme_id_1'},
            'eln_tissue_prep_name': 'tissue_prep_name1',
            'weight_mg': 12,
            'tissue_prep_type': None
        })

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.attributes['eln_tissue_prep_id'], ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'sample': {'id': 'sts_id_2'},
            'species': {'id': 'taxon_id_2'},
            'tolid': {'id': None},
            'eln_tissue_prep_name': 'tissue_prep_name2',
            'weight_mg': 24,
            'dowstream_protocol': 'Plant MagAttract v4'
        })
