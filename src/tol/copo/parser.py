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


CopoApiResource = dict[str, Any]
CopoApiDoc = dict[str, list[CopoApiResource]]


class Parser(ABC):
    """
    Parses COPO API transfer resource `dict`s to `DataObject`
    instances
    """

    def parse_iterable(
        self,
        transfers: Iterable[CopoApiResource]
    ) -> Iterable[DataObject]:
        """
        Parses an `Iterable` of COPO API transfer resources
        """

        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(
        self,
        transfer: CopoApiResource
    ) -> DataObject:
        """
        Parses an individual COPO transfer resource to a
        `DataObject` instance
        """


class DefaultParser(Parser):

    def __init__(self, data_source_dict: dict[str, DataSource]) -> None:
        self.__dict = data_source_dict

    def parse(
            self,
            transfer: CopoApiResource) -> DataObject:
        object_type = transfer.pop('tolsdk-type', 'sample')
        object_id = transfer.pop('copo_id')
        ds = self.__get_data_source(object_type)
        raw_attributes = transfer
        attributes = self.__convert_attributes(object_type, raw_attributes)

        return ds.data_object_factory(
            object_type,
            id_=object_id,
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
                if k in datetime_keys and v is not None and v != ''
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
