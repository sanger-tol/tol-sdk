# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..bold import (
    BoldDataSource,
    create_bold_datasource
)
from ..core import (
    core_data_object
)


def bold(**kwargs) -> BoldDataSource:
    bold = create_bold_datasource(
        bold_url=os.getenv('BOLD_URL', Defaults.BOLD_URL)
        + os.getenv('BOLD_API_PATH', Defaults.BOLD_API_PATH),
        bold_api_key=os.getenv('BOLD_API_KEY')
    )
    core_data_object(bold)
    return bold
