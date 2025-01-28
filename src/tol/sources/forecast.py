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


def forecast():
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1-1BuL2vhg0pe_znGm0X_dVwYYDXu6wCmh7CB39PN0hE',
        'mappings': {
            'forecast': {
                'worksheet_name': 'Demand Libraries',
                'columns': {
                    'id': {
                        'heading': 'Column name',
                        'type': 'int'
                    }
                    'programme': {
                        'heading': 'Programme',
                        'type': 'int'
                    }
                    'type': {
                        'heading': 'Library/ Sequencing',
                        'type': 'str'
                    }
                    'method': {
                        'heading': 'Type',
                        'type': 'str'
                    }
                    'forecast': {
                        'heading': 'Demand Forecast',
                        'type': 'int'
                    }
                    'date': {
                        'heading': 'Date',
                        'type': 'date'
                    }
                    'budget': {
                        'heading': 'Budget',
                        'type': 'float'
                    }
                }
            },
            'header_row': 1,
            'data_start_row': 2
        }
    })
    core_data_object(gsds)
    return gsds
