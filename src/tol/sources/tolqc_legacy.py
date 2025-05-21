# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    core_data_object
)
from ..json import (
    JsonDataSource
)


def tolqc_legacy(**kwargs) -> JsonDataSource:
    tolqc_legacy = JsonDataSource({
        'uri': 'https://tolqc.cog.sanger.ac.uk/data.json',
        'type': 'species',
        'id_attribute': 'taxon',
        'mappings': {
            'group': {
                'heading': 'group',
                'type': 'str'
            },
            'hierarchy_name': {
                'heading': '_name',
                'type': 'str'
            },
            'assembly_stage': {
                'heading': 'asm.stage',
                'type': 'str'
            }
        }
    })
    core_data_object(tolqc_legacy)
    return tolqc_legacy
