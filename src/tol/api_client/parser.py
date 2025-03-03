# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Iterable, Optional

from dateutil.parser import parse as dateutil_parse

from ..core import DataObject

if typing.TYPE_CHECKING:
    from ..core import DataSource


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

    @abstractmethod
    def parse_stats(self, transfer: JsonApiResource) -> dict:
        """
        Parses an individual stats transfer resource to a
        stats dict instance
        """

    @abstractmethod
    def parse_group_stats(self, transfer: JsonApiResource) -> list[dict]:
        """
        Parses a grouped stats transfer resource to a
        list instance
        """


class DefaultParser(Parser):

    def __init__(self, data_source_dict: dict[str, DataSource]) -> None:
        self.__dict = data_source_dict

    def parse(self, transfer: JsonApiResource) -> DataObject:
        type_ = transfer['type']
        ds = self.__get_data_source(type_)
        raw_attributes = transfer.get('attributes')

        attributes = self.__convert_attributes(type_, raw_attributes)

        return ds.data_object_factory(
            transfer.get('type'),
            id_=transfer.get('id'),
            attributes=attributes,
            to_one=self.__parse_to_ones(transfer)
        )

    def parse_stats(self, transfer: JsonApiResource) -> dict:
        type_ = transfer.get('type')
        raw_stats = transfer.get('stats')
        converted_stats = self.__convert_stats(type_, raw_stats)
        return {'stats': converted_stats}

    def parse_group_stats(self, transfer: JsonApiResource) -> Iterable[dict]:
        type_ = transfer.get('type')
        raw_stats = transfer.get('stats')

        return [
            self.__convert_group_stats(type_, raw_stat)
            for raw_stat in raw_stats
        ]

    def __get_data_source(self, type_: str) -> DataSource:
        return self.__dict[type_]

    def __parse_to_ones(
        self,
        transfer: JsonApiResource
    ) -> dict[str, DataObject]:

        return {
            k: self.__parse_to_one(v)
            for k, v in transfer.get('relationships', {}).items()
            if self.__relationship_is_to_one(v)
        }

    def __parse_to_one(
        self,
        v: dict[str, Any] | None
    ) -> DataObject | None:

        if v is None:
            return None
        else:
            return self.parse(v.get('data', {}))

    def __relationship_is_to_one(
        self,
        relation: dict[str, Any] | None
    ) -> bool:

        if relation is None:
            return True

        return isinstance(
            relation.get('data'),
            Mapping
        )

    def __convert_attributes(
        self,
        type_: str,
        attributes: Optional[dict[str, Any]]
    ) -> dict[str, Any]:

        if not attributes:
            return {}

        datetime_keys = self.__get_datetime_keys(type_)

        return {
            k: (
                dateutil_parse(v)
                if k in datetime_keys and v is not None
                else v
            )
            for k, v in attributes.items()
        }

    def __convert_stats(
        self,
        type_: str,
        stats: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        # {'field': {'min': value, 'max': value}
        if not stats:
            return {}

        datetime_keys = self.__get_datetime_keys(type_)

        return {
            fieldname: {
                k: (
                    dateutil_parse(v, ignoretz=True)
                    if fieldname in datetime_keys
                    and v is not None
                    and k in ['min', 'max']
                    else v
                )
                for k, v in fieldstats.items()
            }
            for fieldname, fieldstats in stats.items()
        }

    def __convert_group_stats(
        self,
        type_: str,
        raw_stats: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:

        st = raw_stats.pop('stats')
        count = st.pop('count', None)

        raw_stats['stats'] = self.__convert_stats(type_, st)

        if count is not None:
            raw_stats['stats']['count'] = count

        return raw_stats

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
