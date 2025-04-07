# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Optional

from ._filterable import _Filterable

if typing.TYPE_CHECKING:
    from ..datasource_filter import DataSourceFilter
    from ..session import OperableSession


class Aggregator(_Filterable, ABC):
    """
    Gets aggregations according to the Elastic aggregation specification
    """

    @abstractmethod
    def get_aggregations(
        self,
        object_type: str,
        aggregations: dict[str, Any],
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None
    ) -> dict[str, Any]:
        """
        Gets aggregations according to the Elastic aggregation specification
        """
