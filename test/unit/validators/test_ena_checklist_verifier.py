# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec
from unittest import TestCase
from tol.core import DataObject
from tol.sources.ena import ena
from tol.validators.ena_checklist_verifier import EnaChecklistValidator, EnaChecklistConfig
from tol.validators.incoming_sample_to_ena_sample_converter import IncomingSampleToEnaSampleConverter

    
class TestEnaChecklistVerifier(TestCase):
    config = {
        'ena_checklist_id' :['ERC000053']
    }
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
    validator = EnaChecklistValidator(config=config)
    list(validator.validate(result))
    assert validator.results
