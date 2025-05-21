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


def informatics(**kwargs) -> GoogleSheetDataSource:
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1RKubj10g13INd4W7alHkwcSVX_0CRvNq0-SRe21m-GM',
        'mappings': {
            'tolid': {
                'worksheet_name': 'Status',
                'columns': {
                    'id': {
                        'heading': 'sample',
                        'type': 'str'
                    },
                    'status_summary': {
                        'heading': 'statussummary',
                        'type': 'str'
                    },
                    'status': {
                        'heading': 'status',
                        'type': 'str'
                    },
                    'gscope_coverage': {
                        'heading': 'long read cov (gscope)',
                        'type': 'float'
                    },
                    'estimated_genome_size': {
                        'heading': 'est. size (Mb)',
                        'type': 'float'
                    }

                },
                'header_row': 1,
                'data_start_row': 2
            }
        }
    })
    core_data_object(gsds)
    return gsds
