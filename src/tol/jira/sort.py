# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Optional

from .mapper import JiraMapper


class JiraSorter(JiraMapper, ABC):
    """Runs order_by against a query"""

    @abstractmethod
    def sort(
        self,
        sort_by: Optional[str]
    ) -> str:
        """Sorts a query using the given models"""


class DefaultJiraSorter(JiraSorter):

    def __init__(
        self,
        field_mappings: dict[str, dict[str, str]]
    ) -> None:
        super().__init__(field_mappings)

    def sort(
        self,
        sort_by: str
    ) -> str:
        if sort_by is None:
            desc = None
            term = 'key'
        elif sort_by.startswith('-'):
            desc = True
            term = sort_by[1:]
        else:
            desc = False
            term = sort_by
        mapped_term = self._map_field(term)
        return f' ORDER BY {mapped_term} {"DESC" if desc else "ASC"}'
