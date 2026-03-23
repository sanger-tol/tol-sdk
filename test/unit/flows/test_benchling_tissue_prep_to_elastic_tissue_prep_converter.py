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
    BenchlingTissuePrepToElasticTissuePrepConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['tissue_prep']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceRelational(DataSource, Relational):
    @property
    def supported_types(self):
        return [
            'sample', 'species', 'specimen', 'tolid',
            'tissue_prep'
        ]

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_tissue_prep = RelationshipConfig()
        rc_tissue_prep.to_one = {
            'sample': 'sample',
            'species': 'species',
            'tolid': 'tolid',
        }
        return {'tissue_prep': rc_tissue_prep}

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


class TestBenchlingTissuePrepToElasticTissuePrepConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceRelational(config={})
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
                        'eln_tissue_prep_name': 'tissue_prep_name2',
                        'weight_mg': 24,
                        'dowstream_protocol': 'Plant MagAttract v4'
                        }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'eln_tissue_prep_name': 'tissue_prep_name1',
            'weight_mg': 12,
            'tissue_prep_type': None
        })
        self.assertEqual(ret1.sample.id, 'sts_id_1')
        self.assertEqual(ret1.species.id, 'taxon_id_1')
        self.assertEqual(ret1.tolid.id, 'programme_id_1')

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
        self.assertTrue(ret2.tolid is None)
