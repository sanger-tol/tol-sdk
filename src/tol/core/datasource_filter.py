# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Dict, Tuple


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
    exact: ExactFilter
    wildcard: WildcardFilter

    def __post_init__(self):
        self.exact = ExactFilter(**self.exact)
        self.wildcard = WildcardFilter(
            **self.wildcard
        )

