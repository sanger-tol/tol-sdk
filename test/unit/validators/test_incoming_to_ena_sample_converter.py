# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec
from unittest import TestCase
from tol.core import DataObject
from tol.sources.ena import ena
from tol.validators.incoming_sample_to_ena_sample_converter import IncomingSampleToEnaSampleConverter

    
class TestIncomingSampleToEnaSampleConverter(TestCase):
    
    mock_one: DataObject = create_autospec(DataObject)
    mock_one.attributes = {'ORGANISM_PART': 'WHOLE_ORGANISM',
            'LIFESTAGE': 'ADULT',
            'COLLECTED_BY': 'Dr. Smith',
            'DATE_OF_COLLECTION': '2022-01-01',
            'COLLECTION_LOCATION': 'Country | Region',
            'DECIMAL_LATITUDE': '51.5074',
            'DECIMAL_LONGITUDE': '-0.1278',
            'IDENTIFIED_BY': 'Dr. Jones',
            'HABITAT': 'Forest',
            'IDENTIFIER_AFFILIATION': 'Institute',
            'SEX': 'Male',
            'RELATIONSHIP': 'Parent',
            'SYMBIONT': 'N',
            'COLLECTOR_AFFILIATION': 'Lab',
            'DEPTH': '100',
            'ELEVATION': '200',
            'ORIGINAL_COLLECTION_DATE': '2021-12-31',
            'ORIGINAL_GEOGRAPHIC_LOCATION': 'OldCountry | OldRegion',
            'GAL': 'GAL001',
            'VOUCHER_ID': 'V123',
            'SPECIMEN_ID': 'S123',
            'GAL_SAMPLE_ID': 'GS123',
            'CULTURE_OR_STRAIN_ID': 'CS123'}
    mock_one.id = 'ABC123'
    eds = ena()
    converter = IncomingSampleToEnaSampleConverter(eds.data_object_factory)
    result = converter.convert(mock_one)
    for element in result:
        attrs = element.attributes
        # Check a few key fields
        assert attrs['ENA-CHECKLIST'] == 'ERC000053'
        assert attrs['organism part'] == 'WHOLE ORGANISM'
        assert attrs['lifestage'] == 'ADULT'
        assert attrs['collected by'] == 'Dr. Smith'
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