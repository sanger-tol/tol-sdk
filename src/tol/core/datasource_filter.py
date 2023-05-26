# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


ExactFilter = Dict[str, Any]
ContainsFilter = Dict[str, str]
InListFilter = Dict[str, List[Any]]
RangeFilter = Dict[str, Dict[str, Any]]


@dataclass
class DataSourceFilter:
    """
    Configures the filtering for a DataSource
    """
    exact: Optional[ExactFilter] = None
    contains: Optional[ContainsFilter] = None
    in_list: Optional[InListFilter] = None
    range: Optional[RangeFilter] = None  # noqa A003
