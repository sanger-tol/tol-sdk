# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import os

from tol.core import (
    core_data_object
)
from tol.google_sheets import (
    GoogleSheetDataSource
)


def lr_pacbio():
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1k4_B7_htmlJ762HsoDfZp1lGLJfLuvOX0N9cRh1uQVw',
        'mappings': {
            'sequencing_request': {
                'worksheet_name': 'Lab_Results',
                'columns': {
                    'id': {
                        'heading': 'SANGER SAMPLE ID',
                        'type': 'str'
                    },
                    'library_remaining': {
                        'heading': 'Est. Library\nRemaining\n(ul)',
                        'type': 'str'
                    },
                    'library_remaining_oplc': {
                        'heading': 'Max OPLC From\nRemaining Library\n(@75% recovery)',
                        'type': 'str'
                    },
                    'estimated_max_oplc': {
                        'heading': 'Estimated Maximum OPLC\n(1 cell @50% recovery)',
                        'type': 'int'
                    }
                },
                'header_row': 1,
                'data_start_row': 2
            },
            'sequencing_request_charge': {
                'worksheet_name': 'Charging - Sequencing',
                'columns': {
                    'id': {
                        'heading': 'SANGER SAMPLE ID',
                        'type': 'str'
                    },
                    'portion_of_cell': {
                        'heading': 'Portion of cell',
                        'type': 'str'
                    },
                    'cell_status': {
                        'heading': 'Cell Status',
                        'type': 'str'
                    }
                },
                'header_row': 1,
                'data_start_row': 2
            }

        }
    })
    core_data_object(gsds)
    return gsds
