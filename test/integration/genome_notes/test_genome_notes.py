# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import DataSourceUtils


class TestGenomeNotesDataSource(TestCase):

    def test_attribute_types(self):
        gns = DataSourceUtils.get_datasource('genome_notes_spreadsheet')
        expected_attribute_types = {
            'id': 'str',
            'bioproject': 'str',
            'assembly_accession': 'str',
            'assembly_id': 'str',
            'species_family': 'str',
            'species_species': 'str',
            'tolid': 'str',
            'ncbi_taxon_id': 'int',
            'genome_size': 'float',
            'scaffold_n50_length': 'float',
            'no_of_scaffolds': 'int',
            'contig_n50_length': 'float',
            'total_sequence_length': 'int',
            'total_ungapped_length': 'int',
            'chromosome_count': 'int',
            'assembly_level': 'str',
            'contig_L50': 'int',
            'scaffold_L50': 'int',
            'gc_percent': 'float',
            'genome_coverage': 'int',
            'biosample': 'str',
            'publication_title': 'str',
            'authors': 'str',
            'published_date': 'datetime',
            'pmid': 'int',
        }

        assert 'genome_note' in gns.attribute_types
        assert gns.attribute_types['genome_note'] == expected_attribute_types

    def test_get_list_genome_notes(self):
        gns = DataSourceUtils.get_datasource('genome_notes_spreadsheet')

        ret = gns.get_list('genome_note')
        obj = next(ret, None)
        assert obj is not None, 'No genome_note data available'
        assert obj.id is not None
        assert hasattr(obj, 'bioproject')
        assert hasattr(obj, 'published_date')
        assert hasattr(obj, 'pmid')
