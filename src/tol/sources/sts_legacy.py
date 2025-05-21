# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..sts import (
    StsDataSource
)


def sts_legacy(**kwargs) -> StsDataSource:
    sts_legacy = StsDataSource({
        'url': os.getenv('STS_LEGACY_URL') + os.getenv('STS_LEGACY_API_PATH'),
        'key': os.getenv('STS_API_KEY')
    })
    core_data_object(sts_legacy)
    return sts_legacy
