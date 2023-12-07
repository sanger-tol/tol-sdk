# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable

from .aggregator import Aggregator
from .counter import Counter
from .deleter import Deleter
from .detail_getter import DetailGetter
from .page_getter import PageGetter
from .relational import Relational
from .updater import Updater
from .upserter import Upserter

if typing.TYPE_CHECKING:
    from ...core import DataSource


OPERATOR_MAP: dict[str, type] = {
    'aggregate': Aggregator,
    'count': Counter,
    'delete': Deleter,
    'detailGet': DetailGetter,
    'listGet': PageGetter,
    'relational': Relational,
    'update': Updater,
    'upsert': Upserter
}


OperatorDict = dict[str, list[str]]


class OperatorConfig(ABC):
    """
    Determines which operator methods are supported on
    each of the supported types for a collection of
    `DataSource` instances.
    """

    @abstractmethod
    def to_dict(self) -> dict[str, OperatorDict]:
        """
        Returns a `dict` representation of the supported operators
        for each type of `DataObject`.
        """


class DefaultOperatorConfig(OperatorConfig):
    def __init__(self, *datasources: DataSource) -> None:
        self.__datasources = datasources
        self.__dumped_dict = self.__get_dict()

    def to_dict(self) -> dict[str, OperatorDict]:
        return self.__dumped_dict

    def __get_dict(self) -> dict[str, OperatorDict]:
        pairs = self.__get_pairs()
        return dict(pairs)

    def __get_pairs(
        self
    ) -> Iterable[tuple[str, OperatorDict]]:

        operator_iterables = [
            self.__get_iterable_for_datasource(d)
            for d in self.__datasources
        ]

        return chain(*operator_iterables)

    def __get_iterable_for_datasource(
        self,
        datasource: DataSource
    ) -> Iterable[tuple[str, OperatorDict]]:

        operator_dict = self.__get_dict_for_datasource(
            datasource
        )

        return [
            (t, operator_dict)
            for t in datasource.supported_types
        ]

    def __get_dict_for_datasource(
        self,
        datasource: DataSource
    ) -> OperatorDict:

        operators = [
            k for k, v in OPERATOR_MAP.items()
            if isinstance(datasource, v)
        ]

        return {
            'noauth': operators
        }
