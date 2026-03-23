# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
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


def benchling_googlesheet(**kwargs) -> GoogleSheetDataSource:
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1IyGPD9dF51kUL2mgW6u0r4CNPy7lsTGC2UfD_M58lNo',
        'mappings': {
            'sequencing_request': {
                'worksheet_name': 'Sheet1',
                'columns': {
                    'id': {
                        'heading': 'sequencing_request_id',
                        'type': 'str',
                    },
                    'library_batch_id': {
                        'heading': 'library_batch_id',
                        'type': 'str',
                    },
                },
                'header_row': 1,
                'data_start_row': 2,
            }
        }
    })
    core_data_object(gsds)
    return gsds
