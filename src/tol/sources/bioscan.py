# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from tol.api_client2 import (
    create_api_datasource
)
from tol.core import (
    core_data_object
)


def bioscan():
    bioscan = create_api_datasource(
        os.getenv('BIOSCAN_URL') + os.getenv('BIOSCAN_API_PATH'),
        os.getenv('BIOSCAN_API_KEY')
    )
    core_data_object(bioscan)
    return bioscan
