# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional

from dateutil.parser import parse as dateutil_parse

from ..core import DataObject

if typing.TYPE_CHECKING:
    from ..core import DataSource


LabwhereApiResource = dict[str, Any]
LabwhereApiDoc = dict[str, list[LabwhereApiResource]]


class Parser(ABC):
    """
    Parses LabWhere API transfer resource `dict`s to `DataObject`
    instances
    """

    def parse_iterable(
        self,
        transfers: Iterable[LabwhereApiResource]
    ) -> Iterable[DataObject]:
        """
        Parses an `Iterable` of LabWhere API transfer resources
        """

        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(self, transfer: LabwhereApiResource) -> DataObject:
        """
        Parses an individual LabWhere transfer resource to a
        `DataObject` instance
        """


class DefaultParser(Parser):

    def __init__(self, data_source_dict: dict[str, DataSource]) -> None:
        self.__dict = data_source_dict

    def parse(self, transfer: LabwhereApiResource) -> DataObject:
        type_ = 'location' if 'location_type_id' in transfer else 'location_type'
        ds = self.__get_data_source(type_)
        raw_attributes = transfer

        attributes = self.__convert_attributes(type_, raw_attributes)

        return ds.data_object_factory(
            type_,
            id_=transfer.get('barcode'),
            attributes=attributes
        )

    def __get_data_source(self, type_: str) -> DataSource:
        return self.__dict[type_]

    def __convert_attributes(
        self,
        type_: str,
        attributes: Optional[dict[str, Any]]
    ) -> dict[str, Any]:

        if not attributes:
            return {}
        ds = self.__get_data_source(type_)
        attribute_types = ds.attribute_types.get(
            type_,
            {}
        )

        datetime_keys = self.__get_datetime_keys(type_)

        return {
            k: (
                dateutil_parse(v)
                if k in datetime_keys and v is not None
                else v
            )
            for k, v in attributes.items()
            if k in attribute_types
        }

    def __get_datetime_keys(self, type_: str) -> list[str]:
        ds = self.__get_data_source(type_)
        attribute_types = ds.attribute_types.get(
            type_,
            {}
        )

        return [
            k for k, v in attribute_types.items()
            if self.__value_is_datetime(v)
        ]

    def __value_is_datetime(self, __v: str) -> bool:
        lower_ = __v.lower()

        return 'date' in lower_ or 'time' in lower_
