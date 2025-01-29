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


def finance():
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1k4_B7_htmlJ762HsoDfZp1lGLJfLuvOX0N9cRh1uQVw',
        'mappings': {
            'cost': {
                'worksheet_name': 'Sample financial data',
                'columns': {
                    'project_cost_id': {
                        'heading': 'Proj',
                        'type': 'str'
                    },
                    'study_id': {
                        'heading': 'Cat5',
                        'type': 'int'
                    },
                    'period': {
                        'heading': 'Period(T)',
                        'type': 'date'
                    },
                    'amount': {
                        'heading': 'GBP amnt',
                        'type': 'double'
                    }
                },
                'header_row': 1,
                'data_start_row': 2
            }
        }
    })
    core_data_object(gsds)
    return gsds
