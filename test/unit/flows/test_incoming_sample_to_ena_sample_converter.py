# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import IncomingSampleToEnaSampleConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['upload']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceDestination(DataSource):
    @property
    def supported_types(self):
        return ['upload']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestIncomingSampleToEnaSampleConverter(TestCase):

    def test_convert(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'upload',
            'ABC123',
            attributes={
                'ORGANISM_PART': ['HEAD', 'LEG'],
                'LIFESTAGE': 'ADULT',
                'COLLECTED_BY': ['Dr. Smith'],
                'DATE_OF_COLLECTION': '2022-01-01',
                'COLLECTION_LOCATION': 'Country | Region',
                'DECIMAL_LATITUDE': '51.5074',
                'DECIMAL_LONGITUDE': '-0.1278',
                'IDENTIFIED_BY': ['Dr. Jones'],
                'HABITAT': 'Forest',
                'IDENTIFIER_AFFILIATION': ['Institute'],
                'SEX': 'Male',
                'RELATIONSHIP': 'Parent',
                'SYMBIONT': 'N',
                'COLLECTOR_AFFILIATION': ['Lab'],
                'DEPTH': '100',
                'ELEVATION': '200',
                'ORIGINAL_COLLECTION_DATE': '2021-12-31',
                'ORIGINAL_GEOGRAPHIC_LOCATION': 'OldCountry | OldRegion',
                'GAL': 'GAL001',
                'VOUCHER_ID': 'V123',
                'SPECIMEN_ID': 'S123',
                'GAL_SAMPLE_ID': 'GS123',
                'CULTURE_OR_STRAIN_ID': 'CS123'
            }
        )
        config = IncomingSampleToEnaSampleConverter.Config(
            ena_checklist_id='ERC000053',
            project_name='TOL',
        )
        converter = IncomingSampleToEnaSampleConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        res = next(result)
        attrs = res.attributes
        # Check a few key fields
        assert attrs['ENA-CHECKLIST'] == 'ERC000053'
        assert attrs['organism part'] == 'HEAD | LEG'
        assert attrs['lifestage'] == 'ADULT'
        assert attrs['collected_by'] == 'Dr. Smith'
        assert attrs['collection date'] == '2022-01-01'
        assert attrs['geographic location (country and/or sea)'] == 'Country'
        assert attrs['geographic location (latitude)'] == '51.5074'
        assert attrs['geographic location (latitude) units'] == 'DD'
        assert attrs['geographic location (longitude)'] == '-0.1278'
        assert attrs['geographic location (longitude) units'] == 'DD'
        assert attrs['geographic location (region and locality)'] == 'Region'
        assert attrs['identified_by'] == 'Dr. Jones'
        assert attrs['habitat'] == 'Forest'
        assert attrs['identifier_affiliation'] == 'Institute'
        assert attrs['sex'] == 'Male'
        assert attrs['relationship'] == 'Parent'
        assert attrs['SYMBIONT'] == 'N'
        assert attrs['collecting institution'] == 'Lab'
        assert attrs['geographic location (depth)'] == '100'
        assert attrs['geographic location (depth) units'] == 'm'
        assert attrs['geographic location (elevation)'] == '200'
        assert attrs['geographic location (elevation) units'] == 'm'
        assert attrs['original collection date'] == '2021-12-31'
        assert attrs['original geographic location'] == 'OldCountry | OldRegion'
        assert attrs['GAL'] == 'GAL001'
        assert attrs['specimen_voucher'] == 'V123'
        assert attrs['specimen_id'] == 'S123'
        assert attrs['GAL_sample_id'] == 'GS123'
        assert attrs['culture_or_strain_id'] == 'CS123'

        with self.assertRaises(StopIteration):
            next(result)
