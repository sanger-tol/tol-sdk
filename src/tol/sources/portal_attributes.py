# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
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


def portal_attributes(**kwargs) -> GoogleSheetDataSource:
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1kKta1ziEqAqXd5-ZJmv3PA9lE4kxh6BD4Bpxh0HhxeQ',
        'mappings': {
            'attribute': {
                'worksheet_name': 'Attributes',
                'columns': {
                    'object_type': {
                        'heading': 'object_type',
                        'type': 'str'
                    },
                    'id': {
                        'heading': 'id',
                        'type': 'str'
                    },
                    'name': {
                        'heading': 'name',
                        'type': 'str'
                    },
                    'display_name': {
                        'heading': 'display_name',
                        'type': 'str'
                    },
                    'authoritative': {
                        'heading': 'authoritative',
                        'type': 'boolean'
                    },
                    'available_on_relationships': {
                        'heading': 'available_on_relationships',
                        'type': 'boolean'
                    },
                    'description': {
                        'heading': 'description',
                        'type': 'str'
                    },
                    'source': {
                        'heading': 'source',
                        'type': 'str'
                    }
                },
                'header_row': 5,
                'data_start_row': 6
            }
        }
    })
    core_data_object(gsds)
    return gsds
