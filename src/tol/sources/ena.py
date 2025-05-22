# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..core import (
    core_data_object
)
from ..ena import (
    EnaDataSource,
    create_ena_datasource
)


def ena(**kwargs) -> EnaDataSource:
    ena = create_ena_datasource(
        ena_url=os.getenv('ENA_URL', Defaults.ENA_URL),
        ena_user=os.getenv('ENA_USER'),
        ena_password=os.getenv('ENA_PASSWORD'),
        ena_contact_name=os.getenv('ENA_CONTACT_NAME'),
        ena_contact_email=os.getenv('ENA_CONTACT_EMAIL'),
    )
    core_data_object(ena)
    return ena
