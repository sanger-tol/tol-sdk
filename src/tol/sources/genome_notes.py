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
        'sheet_key': '1OwMsyI8a5WfQf2Y0LHM-SqJ17exjTLjjUDG-ig3aHw0',
        'mappings': {
            'genome_note': {
                'worksheet_name': 'Published record',
                'columns': {
                    'id': {
                        'heading': 'doi',
                        'type': 'str'
                    },
                    'species_name': {
                        'heading': 'species',
                        'type': 'str'
                    },
                    'taxid': {
                        'heading': 'taxid',
                        'type': 'int'
                    },
                    'tolid': {
                        'heading': 'tolid',
                        'type': 'str'
                    },
                    'passed_pr': {
                        'heading': 'Passed_PR',
                        'type': 'boolean'
                    },
                    'assembly_accession': {
                        'heading': 'Accession',
                        'type': 'str'
                    },
                    'date_published': {
                        'heading': 'Date_published',
                        'type': 'datetime',
                        'dayfirst': True
                    },
                    'pmid': {
                        'heading': 'PMID',
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
