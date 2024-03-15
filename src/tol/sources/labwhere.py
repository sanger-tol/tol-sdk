# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..labwhere import (
    LabwhereDataSource,
    create_labwhere_datasource
)


def labwhere() -> LabwhereDataSource:
    labwhere = create_labwhere_datasource(
        labwhere_url=os.getenv('LABWHERE_URL') + os.getenv('LABWHERE_API_PATH'),
    )
    core_data_object(labwhere)
    return labwhere
