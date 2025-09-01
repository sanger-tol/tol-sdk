# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..core import (
    core_data_object
)
from ..s3 import (
    S3DataSource,
    create_s3_datasource
)


def bioscan_image(**kwargs) -> S3DataSource:
    s3ds = create_s3_datasource(
        bucket_name=os.getenv('BIOSCAN_IMAGE_BUCKET_NAME',
                              Defaults.BIOSCAN_IMAGE_BUCKET_NAME),
        prefix=os.getenv('BIOSCAN_IMAGE_PREFIX', Defaults.BIOSCAN_IMAGE_PREFIX),
    )
    core_data_object(s3ds)
    return s3ds
