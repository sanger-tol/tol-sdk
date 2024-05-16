# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

__AndFilterTerm = dict[
    str,
    dict[str, Any]
]


ExactFilter = Dict[str, Any]
ContainsFilter = Dict[str, str]
InListFilter = Dict[str, List[Any]]
RangeFilter = Dict[str, Dict[str, Any]]
AndFilter = dict[
    str,
    __AndFilterTerm
]


@dataclass
class DataSourceFilter:
    """
    Configures the filtering for a DataSource
    """
    exact: Optional[ExactFilter] = None
    contains: Optional[ContainsFilter] = None
    in_list: Optional[InListFilter] = None
    range: Optional[RangeFilter] = None  # noqa A003
    and_: Optional[AndFilter] = None
