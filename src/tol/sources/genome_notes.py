# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import os

from ..core import (
    core_data_object
)
from ..google_sheets import (
    GoogleSheetDataSource
)


def genome_notes(**kwargs) -> GoogleSheetDataSource:
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '12ZgUDOC3x_pH8X84nqhNf1d3E1eS5maB0W5fsJQsCIE',
        'mappings': {
            'genome_note': {
                'worksheet_name': 'Sheet1',
                'columns': {
                    'id': {
                        'heading': 'doi',
                        'type': 'str'
                    },
                    'bioproject': {
                        'heading': 'bioproject',
                        'type': 'str'
                    },
                    'assembly_accession': {
                        'heading': 'assembly_accession',
                        'type': 'str'
                    },
                    'assembly_id': {
                        'heading': 'assembly_id',
                        'type': 'str'
                    },
                    'species_family': {
                        'heading': 'species_family',
                        'type': 'str'
                    },
                    'species_species': {
                        'heading': 'species_species',
                        'type': 'str'
                    },
                    'tolid': {
                        'heading': 'tolid',
                        'type': 'str'
                    },
                    'ncbi_taxon_id': {
                        'heading': 'ncbi_taxon_id',
                        'type': 'int',
                    },
                    'genome_size': {
                        'heading': 'genome_size',
                        'type': 'float'
                    },
                    'scaffold_n50_length': {
                        'heading': 'scaffold_n50_length',
                        'type': 'float'
                    },
                    'no_of_scaffolds': {
                        'heading': 'no_of_scaffolds',
                        'type': 'int'
                    },
                    'contig_n50_length': {
                        'heading': 'contig_n50_length',
                        'type': 'float'
                    },
                    'total_sequence_length': {
                        'heading': 'total_sequence_length',
                        'type': 'int'
                    },
                    'total_ungapped_length': {
                        'heading': 'total_ungapped_length',
                        'type': 'int'
                    },
                    'chromosome_count': {
                        'heading': 'chromosome_count',
                        'type': 'int'
                    },
                    'assembly_level': {
                        'heading': 'assembly_level',
                        'type': 'str',
                    },
                    'contig_L50': {
                        'heading': 'contig_L50',
                        'type': 'int'
                    },
                    'scaffold_L50': {
                        'heading': 'scaffold_L50',
                        'type': 'int'
                    },
                    'gc_percent': {
                        'heading': 'gc_percent',
                        'type': 'float'
                    },
                    'genome_coverage': {
                        'heading': 'genome_coverage',
                        'type': 'int'
                    },
                    'biosample': {
                        'heading': 'biosample',
                        'type': 'str',
                    },
                    'publication_title': {
                        'heading': 'publication_title',
                        'type': 'str'
                    },
                    'authors': {
                        'heading': 'authors',
                        'type': 'str'
                    },
                    'published_date': {
                        'heading': 'published_date',
                        'type': 'datetime',
                        'dayfirst': True
                    },
                    'pmid': {
                        'heading': 'pmid',
                        'type': 'int'
                    }
                },
                'header_row': 1,
                'data_start_row': 2
            }
        }
    })
    core_data_object(gsds)
    return gsds