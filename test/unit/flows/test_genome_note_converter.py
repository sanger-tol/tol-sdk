# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import unittest
from unittest.mock import MagicMock

from tol.flows.converters.genome_note_converter import GenomeNoteConverter


class TestGenomeNoteConverter(unittest.TestCase):
    def setUp(self):
        self.mock_factory = MagicMock()
        self.mock_data_object = MagicMock()
        self.mock_data_object.attributes = {
            'reviewer_reports': 'should be ignored',
            'publication_metadata': 'should be ignored',
            'metadata': {
                'doi': '10.1234/example',
                'title': 'Genome Note',
                'authors': [
                    {'surname': 'Smith', 'given_names': 'John'},
                    {'surname': 'Doe', 'given_names': 'Jane'},
                ],
                'keywords': ['genome', 'note'],
                'background': 'background text',
                'bioproject': 'PRJ123',
            },
            'methods': {
                'sample_acquisition': 'method1',
                'nucleic_acid_extraction': 'method2',
            },
            'assembly_stats': {
                'sequence_report': {
                    'isolate_info': 'iso',
                    'assembly_accession': 'GCA_000001',
                },
                'analysis': {'busco': {}},
                'assembly_graphs': {'kmer': {}},
                'chromosomal_pseudomolecules': ['chr1'],
                'samples': ['sample1'],
                'species': ['species1'],
                'other': {'genome_annotation': 'ann'},
            },
            'software_tools': ['tool1'],
            'references': ['ref1'],
        }
        self.converter = GenomeNoteConverter(self.mock_factory, GenomeNoteConverter.Config())

    def test_convert(self):
        """Test that the converter ignores, renames, and copies attributes correctly."""
        class DummyObj:
            def __init__(self, attributes):
                self.attributes = attributes
        self.mock_factory.side_effect = lambda attributes: DummyObj(attributes)

        result = list(self.converter.convert(self.mock_data_object))
        self.assertEqual(len(result), 1)
        attrs = result[0].attributes

        # Ignored fields should not be present
        self.assertNotIn('reviewer_reports', attrs)
        self.assertNotIn('publication_metadata', attrs)
        # Metadata fields should be present at top level
        self.assertEqual(attrs['doi'], '10.1234/example')
        self.assertEqual(attrs['title'], 'Genome Note')
        self.assertEqual(attrs['keywords'], ['genome', 'note'])
        self.assertEqual(attrs['background'], 'background text')
        self.assertEqual(attrs['bioproject'], 'PRJ123')
        # Authors should be a list of dicts
        self.assertEqual(attrs['authors'], [
            {'surname': 'Smith', 'given_names': 'John'},
            {'surname': 'Doe', 'given_names': 'Jane'},
        ])
        # References should be present
        self.assertEqual(attrs['references'], ['ref1'])
        # Methods should be renamed and present
        self.assertEqual(attrs['method_sample_acquisition'], 'method1')
        self.assertEqual(attrs['method_nucleic_acid_extraction'], 'method2')
        # Sequence report fields should be at top level
        self.assertEqual(attrs['isolate_info'], 'iso')
        self.assertEqual(attrs['assembly_accession'], 'GCA_000001')
        # Analysis and assembly_graphs should be renamed
        self.assertIn('assembly_stats_analysis', attrs)
        self.assertIn('assembly_stats_assembly_graphs', attrs)
        # Remaining assembly_stats fields
        self.assertEqual(attrs['chromosomal_pseudomolecules'], ['chr1'])
        self.assertEqual(attrs['samples'], ['sample1'])
        self.assertEqual(attrs['species'], ['species1'])
        self.assertEqual(attrs['other'], {'genome_annotation': 'ann'})
        # As-is field should be present
        self.assertEqual(attrs['software_tools'], ['tool1'])


if __name__ == '__main__':
    unittest.main()
