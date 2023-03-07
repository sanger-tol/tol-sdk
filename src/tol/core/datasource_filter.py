# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, Optional


ExactFilter = Dict[str, Any]
WildcardFilter = Dict[str, str]


@dataclass
class DataSourceFilter:
    """
    Configures the filtering for a DataSource
    """
    exact: Optional[ExactFilter] = None
    wildcard: Optional[WildcardFilter] = None
