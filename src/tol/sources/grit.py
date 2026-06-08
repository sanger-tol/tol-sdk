# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..jira import JiraDataSource
from .registry import default_registry


def grit(**kwargs) -> JiraDataSource:
    return default_registry.create('grit', **kwargs)
