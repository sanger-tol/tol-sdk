# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..gap import (
    GapDataSource
)


def gap():
    gap = GapDataSource({
        'uri': 's3://tolqc/data.json',
        'type': 'assembly',
        'id_attribute': 'accession',
        's3_host': 'cog.sanger.ac.uk',
        's3_access_key': os.getenv('MINIO_ACCESS_KEY'),
        's3_secret_key': os.getenv('MINIO_SECRET_KEY'),
        'mappings': {
            '': {
                'heading': '',
                'type': ''
            }
        }
    })
    core_data_object(gap)
    return gap
