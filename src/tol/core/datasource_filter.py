# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class WildcardFilter:
    """
    Wildcard filtering, i.e. by substring
    """
    terms: Dict[str, str]


@dataclass
class ExactFilter:
    """
    Exact filtering on multiple datatypes
    """
    terms: Dict[str, Any]


@dataclass
class DataSourceFilter:
    """
    Configures the filtering for a DataSource
    """
    exact: Optional[ExactFilter] = None
    wildcard: Optional[WildcardFilter] = None

    def __post_init__(self):
        if self.exact is not None:
            self.exact = ExactFilter(**self.exact)
        if self.wildcard is not None:
            self.wildcard = WildcardFilter(
            **self.wildcard
        )

