# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
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
    ElasticSampleToBoldSampleConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['sample', 'specimen']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'sts_specimen': 'specimen',
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


class TestElasticSampleToBoldSampleConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSampleToBoldSampleConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticSampleToBoldSampleConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        specimen = CoreDataObject(
            id_='specimen1',
            type_='specimen',
            attributes={}
        )

        obj1 = CoreDataObject(
            id_='1234',
            type_='sample',
            attributes={
                'sts_gal_name': 'GENOME ACQUISITION LABORATORY',
                'sts_gal_abbreviation': 'GAL',
                'sts_organism_part': ['LEG', 'ARM'],
                'sts_rackid': 'GAL_1234_5678',
                'sts_CONTRIBUTORS':
                    'Person One;Institution One;p1@i1.ac.uk;primary contact|'
                    'Person Two;Institution Two;p2@i2.ac.uk;plated specimens',
                'sts_col_date': datetime(2024, 1, 1),
                'sts_COUNTRY_OF_COLLECTION': 'UNITED KINGDOM',
                'sts_latitude': '1.23456',
                'sts_longitude': '54.321123',
                'sts_COLLECTION_METHOD': 'MALAISE_TRAP'
            },
            to_one={
                'sts_specimen': specimen
            }
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='sample',
            attributes={}
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('1234', ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'bold_recordset_code_arr': 'GAL',
            'sampleid': 'specimen1',
            'fieldid': '',
            'inst': 'Wellcome Sanger Institute',
            'phylum': 'Arthropoda',
            'class': '',
            'order': '',
            'short_note': 'GENOME ACQUISITION LABORATORY - GAL',
            'notes': '',
            'voucher_type': '',
            'tissue_type': 'LEG | ARM',
            'collectors': 'Person One, Person Two',
            'collection_date_start': '2024-01-01',
            'country/ocean': 'United Kingdom',
            'province/state': '',
            'coord': '1.23456,54.321123',
            'elev': '',
            'elev_accuracy': '',
            'collection_date_end': '',
            'sampling_protocol': 'Malaise Trap'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret1 = next(converteds)
        self.assertEqual('test2', ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'bold_recordset_code_arr': '',
            'sampleid': '',
            'fieldid': '',
            'inst': 'Wellcome Sanger Institute',
            'phylum': 'Arthropoda',
            'class': '',
            'order': '',
            'short_note': '',
            'notes': '',
            'voucher_type': '',
            'tissue_type': '',
            'collectors': '',
            'collection_date_start': '',
            'country/ocean': '',
            'province/state': '',
            'coord': '',
            'elev': '',
            'elev_accuracy': '',
            'collection_date_end': '',
            'sampling_protocol': ''
        })
        with self.assertRaises(StopIteration):
            next(converteds)
