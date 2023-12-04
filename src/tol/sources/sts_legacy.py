# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from tol.core import (
    core_data_object
)
from tol.sts import (
    StsDataSource
)


def sts_legacy():
    sts_legacy = StsDataSource({
        'url': os.getenv('STS_URL') + os.getenv('STS_API_PATH'),
        'key': os.getenv('STS_API_KEY')
    })
    core_data_object(sts_legacy)
    return sts_legacy
