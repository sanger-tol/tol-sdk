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


def bioscan_extra(**kwargs) -> GoogleSheetDataSource:
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1XiKKnz8O-GcQ5ww19m1_1Gk7shidUTIvzidY47-F3hs',
        'mappings': {
            'pantheon_species': {
                'worksheet_name': 'NEW_PANTHEON',
                'columns': {
                    'id': {
                        'heading': 'Species',
                        'type': 'str'
                    },
                    'vernacular': {
                        'heading': 'Pantheon:Vernacular',
                        'type': 'str'
                    },
                    'current_conservation_status': {
                        'heading': 'Pantheon:Conservation Status Description',
                        'type': 'str'
                    },
                    'larval_feeding_guild': {
                        'heading': 'Pantheon:Larval feeding guild',
                        'type': 'str'
                    },
                    'adult_feeding_guild': {
                        'heading': 'Pantheon:Adult feeding guild',
                        'type': 'str'
                    },
                    'broad_biotope_habitat_resources': {
                        'heading': 'Pantheon:Broad Biotope, Habitat, Resources',
                        'type': 'str'
                    },
                    'specific_assemblage_type': {
                        'heading': 'Pantheon:Specific assemblage type',
                        'type': 'str'
                    },
                    'link_to_assemblage': {
                        'heading': 'Link to assemblage',
                        'type': 'str'
                    },
                    'associations': {
                        'heading': 'Pantheon:Associations',
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
