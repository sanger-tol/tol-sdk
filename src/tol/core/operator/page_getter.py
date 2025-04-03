# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional, Tuple

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..data_object import DataObject
    from ..datasource_filter import DataSourceFilter
    from ..session import OperableSession


class PageGetter(_Filterable, ABC):
    """
    Gets pages of DataObject instances.
    """

    @abstractmethod
    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Tuple[Iterable[DataObject], int]:
        """
        For a specified object_type, of the given page_size
        and page_number (starting from 1), returns a tuple of:

        - An Iterable of DataObject instances
        - The total number of DataObjects that matches the filter
        """
