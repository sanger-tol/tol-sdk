# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

import responses

from tol.bold import BoldDataSource
from tol.core import (
    DataSourceError,
    DataSourceFilter,
    core_data_object
)


class TestBoldDataSource(TestCase):

    @responses.activate
    def test_get_list(self):
        bds = BoldDataSource({
            'url': 'http://bold.local'
        })
        core_data_object(bds)

        mock_response_from_bold = {
            'bold_records': {
                'records': {
                    'ABC001-19': {
                        'record_id': '12345678',
                        'processid': 'ABC001-19',
                        'bin_uri': 'BOLD:ABA9789',
                        'specimen_identifiers': {
                            'sampleid': 'SAM12345678',
                            'catalognum': 'SPEC1',
                            'fieldnum': 'F1',
                            'institution_storing': 'An institute'
                        },
                        'taxonomy': {
                            'identification_provided_by': 'A person',
                            'identification_method': 'Guessed',
                            'phylum': {
                                'taxon': {
                                    'taxID': '20',
                                    'name': 'Arthropoda'
                                }
                            }
                        }
                    },
                    'ABC001-20': {
                        'record_id': '12345679',
                        'processid': 'ABC001-20',
                        'bin_uri': 'BOLD:ABA9789',
                        'specimen_identifiers': {
                            'sampleid': 'SAM12345679',
                            'catalognum': 'SPEC2',
                            'fieldnum': 'F2',
                            'institution_storing': 'An institute'
                        },
                        'taxonomy': {
                            'identification_provided_by': 'A person',
                            'identification_method': 'Guessed',
                            'phylum': {
                                'taxon': {
                                    'taxID': '20',
                                    'name': 'Arthropoda'
                                }
                            }
                        }
                    }
                }
            }
        }
        responses.add(responses.GET, 'http://bold.local/index.php/API_Public/specimen',
                      json=mock_response_from_bold, status=200)

        with self.assertRaises(DataSourceError):
            bds.get_list('index')

        f = DataSourceFilter()
        with self.assertRaises(DataSourceError):
            bds.get_list('sample', object_filters=f)

        f.in_list = {'container': ['ABC']}
        with self.assertRaises(DataSourceError):
            bds.get_list('sample', object_filters=f)
        f.exact = {'container': 'ABC'}

        returned = bds.get_list('sample', object_filters=f)
        first = next(returned)
        self.assertEqual({'record_id': '12345678',
                          'processid': 'ABC001-19',
                          'bin_uri': 'BOLD:ABA9789',
                          'specimen_identifiers_sampleid': 'SAM12345678',
                          'specimen_identifiers_catalognum': 'SPEC1',
                          'specimen_identifiers_fieldnum': 'F1',
                          'specimen_identifiers_institution_storing': 'An institute',
                          'taxonomy_identification_provided_by': 'A person',
                          'taxonomy_identification_method': 'Guessed',
                          'taxonomy_phylum_taxon_taxID': '20',
                          'taxonomy_phylum_taxon_name': 'Arthropoda'},
                         first.attributes)
        second = next(returned)
        self.assertEqual({'record_id': '12345679',
                          'processid': 'ABC001-20',
                          'bin_uri': 'BOLD:ABA9789',
                          'specimen_identifiers_sampleid': 'SAM12345679',
                          'specimen_identifiers_catalognum': 'SPEC2',
                          'specimen_identifiers_fieldnum': 'F2',
                          'specimen_identifiers_institution_storing': 'An institute',
                          'taxonomy_identification_provided_by': 'A person',
                          'taxonomy_identification_method': 'Guessed',
                          'taxonomy_phylum_taxon_taxID': '20',
                          'taxonomy_phylum_taxon_name': 'Arthropoda'},
                         second.attributes)
        with self.assertRaises(StopIteration):
            next(returned)
