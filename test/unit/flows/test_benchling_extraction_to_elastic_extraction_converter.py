# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
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
    BenchlingExtractionToElasticExtractionConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['extraction']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return ['extraction', 'sample', 'species', 'specimen', 'tolid', 'tissue_prep']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_extraction = RelationshipConfig()
        rc_extraction.to_one = {
            'sample': 'sample',
            'species': 'species',
            'specimen': 'specimen',
            'tolid': 'tolid',
            'tissue_prep': 'tissue_prep'
        }
        return {'extraction': rc_extraction}

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


class TestBenchlingExtractionToElasticExtractionConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
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
            'eln_tissue_prep_name': 'tissue_prep_name1'
        })
        self.assertEqual(ret1.sample.id, 'sts_id_1')
        self.assertEqual(ret1.species.id, 'taxon_id_1')
        self.assertEqual(ret1.specimen.id, 'specimen_id_1')
        self.assertEqual(ret1.tolid.id, 'programme_id_1')
        self.assertEqual(ret1.tissue_prep.id, 'tissue_prep_id_1')

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'eln_tissue_prep_name': 'tissue_prep_name2',
            'weight_mg': 24,
            'dowstream_protocol': 'Plant MagAttract v4'
        })
        self.assertEqual(ret2.sample.id, 'sts_id_2')
        self.assertEqual(ret2.species.id, 'taxon_id_2')
        self.assertEqual(ret2.specimen.id, 'specimen_id_2')
        self.assertTrue(ret2.tolid is None)
        self.assertEqual(ret2.tissue_prep.id, 'tissue_prep_id_2')
