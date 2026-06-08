# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from datetime import date, datetime
from json import dumps
from typing import Any, Callable, Optional

from ..core import DataSourceFilter
from ..core.filter_strategy import FilterStrategy


class ApiFilter(ABC):
    """
    Converts instances of `DataSourceFilter` to a
    valid JSON:API filter dump.
    """

    @abstractmethod
    def dumps(self, filter_: DataSourceFilter) -> Optional[str]:
        """
        Emit a filter string from a `DataSourceFilter` instance
        """


def date_serial(v: Any) -> Any:
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


DictDumper = Callable[[dict[str, Any]], str]
default_dict_dumper: DictDumper = lambda d: dumps(
    d,
    separators=(',', ':'),
    default=date_serial
)


class ApiFilterStrategy(FilterStrategy[str]):
    """Converts a DataSourceFilter to a JSON:API filter string."""

    __KEYS = ['exact', 'contains', 'in_list', 'range', 'and_']

    def __init__(
        self,
        dict_dumper: DictDumper = default_dict_dumper
    ) -> None:
        self.__dict_dumper = dict_dumper

    def convert(self, object_type, object_filters=None):
        if object_filters is None:
            return None
        pairs = (
            (k, getattr(object_filters, k))
            for k in self.__KEYS
        )
        __dict = {k: v for k, v in pairs if v is not None}
        return self.__dict_dumper(__dict)


class DefaultApiFilter(ApiFilter):

    __KEYS = ['exact', 'contains', 'in_list', 'range', 'and_']

    def __init__(
        self,
        dict_dumper: DictDumper = default_dict_dumper
    ) -> None:
        self.__strategy = ApiFilterStrategy(dict_dumper)

    def dumps(self, filter_: DataSourceFilter) -> Optional[str]:
        return self.__strategy.convert(None, filter_)
