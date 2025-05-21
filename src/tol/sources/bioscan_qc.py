# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
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


def bioscan_qc(**kwargs) -> GoogleSheetDataSource:
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1_2lZ5nah_xadTQPhiTkNC5xNEa9VqK-u59Lu2okMD3U',
        'mappings': {
            'specimen': {
                'worksheet_name': 'SANGER_QC',
                'columns': {
                    'id': {
                        'heading': 'SPECIMEN_ID',
                        'type': 'str'
                    },
                    'sanger_qc_result': {
                        'heading': 'Sanger QC Result',
                        'type': 'str'
                    },
                    'sanger_qc_description': {
                        'heading': 'Sanger QC Description',
                        'type': 'str'
                    },
                },
                'header_row': 1,
                'data_start_row': 2
            },
            'uksi_entry': {
                'worksheet_name': 'UKSI_LIST',
                'columns': {
                    'id': {
                        'heading': 'RECOMMENDED_SCIENTIFIC_NAME',
                        'type': 'str'
                    },
                    'uksi_name_status': {
                        'heading': 'UKSI Name Status',
                        'type': 'str'
                    },
                },
                'header_row': 1,
                'data_start_row': 2
            }
        }
    })
    core_data_object(gsds)
    return gsds
