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
                    # 'id': {
                    #     'heading': 'SANGER SAMPLE ID',
                    #     'type': 'str'
                    # },
                    'project': {
                        'heading': 'Proj',
                        'type': 'str'
                    },
                    'cat5': {
                        'heading': 'Cat5',
                        'type': 'int'
                    },
                    'transaction_date': {
                        'heading': 'Trans date',
                        'type': 'datetime'
                    },
                    'currency': {
                        'heading': 'Cur',
                        'type': 'str'
                    },
                    'currency_amount': {
                        'heading': 'Curr. amnt',
                        'type': 'datetime'
                    },
                    'GBP_amount': {
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
