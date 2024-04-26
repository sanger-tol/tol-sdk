# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
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
    StsSampleProjectToElasticSampleConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sample_project', 'sample', 'project',
                'location', 'gal', 'sampleset', 'specimen']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample_project = RelationshipConfig()
        rc_sample_project.to_one = {
            'sample': 'sample',
            'project': 'project'
        }
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'location': 'location',
            'gal': 'gal',
            'sampleset': 'sampleset',
            'specimen': 'specimen'
        }
        return {
            'sample_project': rc_sample_project,
            'sample': rc_sample
        }

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


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestStsSampleProjectToElasticSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsSampleProjectToElasticSampleConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        project = CoreDataObject(
            id_='test_project',
            type_='project',
            attributes={'programme': 'test_programme'}
        )
        location = CoreDataObject(
            id_='test_gal',
            type_='location',
            attributes={
                'location': 'Country | County | Town',
                'lat': 12.345678,
                'long': 23.456789,
                'elevation': 65,
                'depth': 200
            }
        )
        gal = CoreDataObject(
            id_='test_gal',
            type_='gal',
            attributes={
                'name': 'Test Gal',
                'abbreviation': 'TESTGAL'
            }
        )
        specimen = CoreDataObject(
            id_='test_specimen',
            type_='specimen',
            attributes={}
        )
        sampleset = CoreDataObject(
            id_='test_sampleset',
            type_='sampleset',
            attributes={}
        )
        sample = CoreDataObject(
            id_='test_sample',
            type_='sample',
            attributes={
                'col_date': '2020-02-02',
                'original_collection_date': '2011-01-01 12:00:00',
                'pre_date': '2000-12-12',
                'public_name': 'xxTesTest1',
                'other': 'another'
            },
            to_one={
                'location': location,
                'gal': gal,
                'specimen': specimen,
                'sampleset': sampleset
            }
        )
        sample_project = CoreDataObject(
            id_='test_sample_project',
            type_='sample_project',
            attributes={},
            to_one={
                'sample': sample,
                'project': project
            }
        )
        converteds = converter.convert(sample_project)
        ret1 = next(converteds)
        self.assertEqual('test_sample', ret1.id)
        self.assertEqual('sample', ret1.type)
        self.assertEqual(ret1.attributes, {
            'project': ['test_project'],
            'programme': ['test_programme'],
            'collection_country': 'Country',
            'collection_locality': 'County | Town',
            'latitude': 12.345678,
            'longitude': 23.456789,
            'elevation': 65,
            'depth': 200,
            'gal_abbreviation': 'TESTGAL',
            'gal_name': 'Test Gal',
            'specimen': {'id': 'test_specimen'},
            'sampleset_id': 'test_sampleset',
            'col_date': datetime.datetime(2020, 2, 2),
            'original_collection_date': datetime.datetime(2011, 1, 1, 12),
            'pre_date': datetime.datetime(2000, 12, 12),
            'tolid': {'id': 'xxTesTest1'},
            'public_name': None,
            'other': 'another'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
