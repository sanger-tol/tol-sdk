# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Iterable

from .misc import PseudoObject
from ..core import DataObject


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
    def parse(self, transfer: JsonApiResource) -> DataObject:
        return PseudoObject(
            transfer.get('type'),
            id_=transfer.get('id'),
            attributes=transfer.get('attributes'),
            to_ones=self.__parse_to_ones(transfer)
        )

    def __parse_to_ones(
        self,
        transfer: JsonApiResource
    ) -> dict[str, DataObject]:

        return {
            k: self.parse(v.get('data', {}))
            for k, v in transfer.get('relationships', {}).items()
            if self.__relationship_is_to_one(v)
        }

    def __relationship_is_to_one(
        self,
        relationship: dict[str, Any]
    ) -> bool:

        return isinstance(
            relationship.get('data'),
            Mapping
        )
