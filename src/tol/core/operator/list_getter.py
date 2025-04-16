# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..data_object import DataObject
    from ..datasource_filter import DataSourceFilter
    from ..session import OperableSession


class ListGetter(_Filterable, ABC):
    """
    Gets an Iterable of DataObject instances.
    """

    @abstractmethod
    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[DataObject]:
        """
        Gets an Iterable of DataObject instances of the given
        type, according to the given DataSourceFilter.
        """
