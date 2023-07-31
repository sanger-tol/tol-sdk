# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable

from ...core import DataSource
from ...core.operator import (
    Aggregator,
    Deleter,
    DetailGetter,
    PageGetter,
    Updater,
    Upserter
)


OperatorDict = dict[str, list[str]]
AllOperationsDict = dict[str, OperatorDict]


class OperationsConfig(ABC):
    """
    Determines which operator methods are supported on
    each of the supported types for a collection of
    `DataSource` instances.
    """

    @abstractmethod
    def to_dict(self) -> AllOperationsDict:
        """
        Returns a `dict` representation of the supported operations
        for each type of `DataObject`.
        """


class DefaultOperationsConfig(OperationsConfig):

    __OPERATOR_MAP: dict[str, type] = {
        'aggregate': Aggregator,
        'delete': Deleter,
        'detailGet': DetailGetter,
        'listGet': PageGetter,
        'update': Updater,
        'upsert': Upserter
    }

    def __init__(self, *datasources: DataSource) -> None:
        self.__datasources = datasources
        self.__dumped_dict = self.__get_dict()

    def to_dict(self) -> AllOperationsDict:
        return self.__dumped_dict

    def __get_dict(self) -> AllOperationsDict:
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
            k for k, v in self.__OPERATOR_MAP.items()
            if isinstance(datasource, v)
        ]

        return {
            'noauth': operators
        }
