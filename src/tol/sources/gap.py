# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    core_data_object
)
from ..json import (
    S3JsonDataSource
)


def gap():
    gap = S3JsonDataSource({
        'uri': 's3://tolqc/data.json',
        'type': 'assembly',
        'id_attribute': '',
        'mappings': {
        }
    })
    core_data_object(gap)
    return gap
