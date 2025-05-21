# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from .defaults import Defaults
from ..core import (
    core_data_object
)
from ..jira import (
    JiraDataSource,
    create_jira_datasource
)


def grit(**kwargs) -> JiraDataSource:
    grit = create_jira_datasource(
        jira_url=os.getenv('JIRA_URL', Defaults.JIRA_URL),
        jira_api_key=os.getenv('JIRA_API_KEY')
    )
    core_data_object(grit)
    return grit
