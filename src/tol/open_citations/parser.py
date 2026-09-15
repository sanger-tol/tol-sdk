# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional

from ..core import DataObject

if typing.TYPE_CHECKING:
    from ..core import DataSource


OpenCitationsApiResource = dict[str, Any]
OpenCitationsApiDoc = dict[str, list[OpenCitationsApiResource]]


class Parser(ABC):
    """
    Parses OpenCitations API transfer resource `dict`s to `DataObject`
    instances.
    """

    def parse_iterable(
        self,
        object_type: str,
        transfers: Iterable[OpenCitationsApiResource]
    ) -> Iterable[DataObject]:
        """
        Parse an `Iterable` of OpenCitations API transfer resources.
        """
        return (
            self.parse(object_type, t) for t in transfers
        )

    @abstractmethod
    def parse(
        self,
        object_type: str,
        transfer: OpenCitationsApiResource
    ) -> DataObject:
        """
        Parses an individual OpenCitations API transfer resource to a
        `DataObject` instance.
        """


class DefaultParser(Parser):

    def __init__(
        self,
        data_source_dict: dict[str, 'DataSource']
    ) -> None:
        self.__dict = data_source_dict

    def parse(
        self,
        object_type: str,
        transfer: OpenCitationsApiResource
    ) -> DataObject:
        type_ = object_type
        ds = self.__get_data_source(type_)
        raw_attributes = transfer
        id_ = self.__get_id(type_, transfer)
        attributes = self.__convert_attributes(type_, raw_attributes)

        return ds.data_object_factory(
            type_,
            id_=id_,
            attributes=attributes,
        )

    def __get_data_source(self, type_: str) -> 'DataSource':
        if type_ not in self.__dict:
            raise ValueError(f'Data source not found for {type_}')
        return self.__dict[type_]

    def __get_id(self, type_: str, transfer: OpenCitationsApiResource) -> str:
        if type_ == 'meta':
            return self.__get_doi_id(transfer['id'])
        raise ValueError(f'Unsupported object type: {type_}')

    def __get_doi_id(self, identifier: str) -> str:
        identifier = identifier.strip()
        if not identifier:
            return identifier

        for token in self.__split_identifiers(identifier):
            if token.lower().startswith('doi:'):
                return token[4:]

        if identifier.lower().startswith('doi:'):
            return identifier[4:]

        return identifier

    def __split_identifiers(self, identifier: str) -> list[str]:
        return [token.strip() for token in identifier.split() if token.strip()]

    def __convert_attributes(
        self,
        type_: str,
        attributes: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        ret = {}
        if attributes is None:
            return ret

        allowed_attributes = self.__dict[type_].attribute_types[type_]

        for key, value in attributes.items():
            if key in allowed_attributes:
                ret[key] = value

        return ret
