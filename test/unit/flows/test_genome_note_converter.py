# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import (
    DataSource,
    core_data_object,
)
from tol.flows.converters.genome_note_converter import GenomeNoteConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['genome_note']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestGenomeNoteConverter(TestCase):

    def test_convert(self):
        destination = _MockDataSource(config={})
        core_data_object(destination)

        converter = GenomeNoteConverter(
            data_object_factory=destination.data_object_factory,
            config=GenomeNoteConverter.Config(),
        )

        CoreDataObject = destination.data_object_factory  # noqa N806

        obj = CoreDataObject(
            id_='input_id',
            type_='genome_note',
            attributes={
                'reviewer_reports': 'should be ignored',
                'publication_metadata': 'should be ignored',
                'metadata': {
                    'doi': '10.1234/example',
                    'title': 'Genome Note',
                    'authors': [
                        {
                            'surname': 'Smith',
                            'given_names': 'John',
                        },
                        {
                            'surname': 'Doe',
                            'given_names': 'Jane',
                        },
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
                    'analysis': {
                        'busco': {},
                    },
                    'assembly_graphs': {
                        'kmer': {},
                    },
                    'chromosomal_pseudomolecules': ['chr1'],
                    'samples': ['sample1'],
                    'species': [
                        {
                            'scientific_name': 'Species one',
                            'taxon_id': '12345',
                        },
                    ],
                    'other': {
                        'genome_annotation': 'ann',
                    },
                },
                'software_tools': ['tool1'],
                'references': ['ref1'],
            },
        )

        converteds = converter.convert(obj)
        ret = next(converteds)

        self.assertEqual(ret.type, 'genome_note')
        self.assertEqual(ret.id, '10.1234/example')

        self.assertEqual(ret.attributes, {
            'data_availability': '',
            'title': 'Genome Note',
            'abstract': '',
            'keywords': ['genome', 'note'],
            'background': 'background text',
            'bioproject': 'PRJ123',
            'authors': [
                'John Smith',
                'Jane Doe',
            ],
            'references': ['ref1'],
            'method_sample_acquisition': 'method1',
            'method_nucleic_acid_extraction': 'method2',
            'isolate_info': 'iso',
            'assembly_accession': 'GCA_000001',
            'assembly_stats_analysis': {
                'busco': {},
            },
            'assembly_stats_assembly_graphs': {
                'kmer': {},
            },
            'chromosomal_pseudomolecules': ['chr1'],
            'samples': ['sample1'],
            'other': {
                'genome_annotation': 'ann',
            },
            'species_scientific_name': 'Species one',
            'species_taxon_id': '12345',
            'software_tools': ['tool1'],
        })

        with self.assertRaises(StopIteration):
            next(converteds)
