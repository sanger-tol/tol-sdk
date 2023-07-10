# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from ..core import DataObject, DataObjectFactory


JsonApiResource = dict[str, Any]
JsonApiDoc = dict[str, list[JsonApiResource]]


class Parser(ABC):
    """
    Parses JSON:API transfer resource `dict`s to `DataObject`
    instances
    """

    def parse_iterable(
        self,
        transfers: Iterable[JsonApiResource]
    ) -> Iterable[DataObject]:
        """
        Parses an `Iterable` of JSON:API transfer resources
        """

        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(self, transfer: JsonApiResource) -> DataObject:
        """
        Parses an individual JSON:API transfer resource to a
        `DataObject` instance
        """


class DefaultParser(Parser):

    def __init__(
        self,
        data_object_factory: DataObjectFactory
    ) -> None:

        self.__data_object_factory = data_object_factory

    def parse(self, transfer: JsonApiResource) -> DataObject:

        return self.__data_object_factory(
            transfer.get('type'),
            id_=transfer.get('id'),
            data=transfer.get('attributes')
        )
