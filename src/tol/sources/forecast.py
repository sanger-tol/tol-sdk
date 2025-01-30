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
    common_columns = {
        'programme': {
            'heading': 'Programme',
            'type': 'str'
        },
        'analysis_type': {
            'heading': 'Library/ Sequencing',
            'type': 'str'
        },
        'preparation_type': {
            'heading': 'Type',
            'type': 'str'
        },
        'forecast': {
            'heading': 'Demand forecast ',
            'type': 'int'
        },
        'date': {
            'heading': 'Date',
            'type': 'date'
        },
        'budget': {
            'heading': 'Budget',
            'type': 'float'
        }
    }

    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1-1BuL2vhg0pe_znGm0X_dVwYYDXu6wCmh7CB39PN0hE',
        'mappings': {
            'forecast_lib': {
                'worksheet_name': 'Demand Libraries',
                'columns': common_columns,
                'header_row': 1,
                'data_start_row': 2,
                'id_prefix': 'L'
            },
            'forecast_seq': {
                'worksheet_name': 'Demand Sequencing',
                'columns': common_columns,
                'header_row': 1,
                'data_start_row': 2,
                'id_prefix': 'S'
            }
        }
    })

    core_data_object(gsds)
    return gsds
