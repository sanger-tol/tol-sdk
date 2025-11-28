# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from dateutil.parser import parse as dateutil_parse

from ..core import DataObject, ReqFieldsTree

if typing.TYPE_CHECKING:
    from ..core import DataSource


JsonApiResource = dict[str, Any]
JsonApiDoc = dict[str, list[JsonApiResource]]


class Parser(ABC):
    """
    Parses JSON:API transfer resource `dict`s to `DataObject`
    instances
    """

    @abstractmethod
    def parse_json_doc(self, transfer: JsonApiDoc) -> Iterable[DataObject]:
        """
        Parses a JSON:API document, which includes a `data` array and possibly
        an `included` array of related objects, returning an list of
        `DataObject`.
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
    def __init__(
        self,
        data_source_dict: dict[str, DataSource],
        requested_tree: ReqFieldsTree | None = None,
    ) -> None:
        self.__ds_dict = data_source_dict
        self.__requested_tree = requested_tree

    def parse_json_doc(
        self,
        transfer: JsonApiDoc,
    ) -> Iterable[DataObject]:
        data_objects = list(self.__parse_iterable(transfer['data']))
        if tree := self.__requested_tree:
            included = DataObjectCatalog(self.__parse_iterable(transfer.get('included')))
            for obj in data_objects:
                self.__link_related_obejcts(tree, included, obj)
        return data_objects

    def __link_related_obejcts(
        self,
        tree: ReqFieldsTree,
        included: DataObjectCatalog,
        data_object: DataObject,
    ) -> None:
        """
        Using the `ReqFieldsTree` recursively replaces related stub
        `DataObject`s with `DataObject`s from the `incldued`
        `DataObjectCatalog` which were built from the JSON:API "included"
        array.
        """
        for name, sub_tree in tree.sub_trees():
            if name in tree.to_one_names():
                if (related := data_object._to_one_objects.get(name)) and (
                    inc := included.fetch(related)
                ):
                    # Link the to-one object
                    setattr(data_object, name, inc)
                    self.__link_related_obejcts(sub_tree, included, inc)
            elif related := data_object._to_many_objects.get(name):
                # Link each to-many object
                for i, rel in enumerate(related):
                    if inc := included.fetch(rel):
                        related[i] = inc
                        self.__link_related_obejcts(sub_tree, included, inc)

    def __parse_iterable(
        self,
        transfer: list[JsonApiResource],
    ) -> Iterable[DataObject]:
        if transfer:
            if isinstance(transfer, list):
                for json_res in transfer:
                    yield self.__parse(json_res)
            else:
                yield self.__parse(transfer)

    def __parse(self, transfer: JsonApiResource) -> DataObject:
        type_ = transfer['type']
        ds = self.__get_data_source(type_)
        attributes = self.__convert_attributes(type_, transfer.get('attributes'))
        to_one, to_many = self.__parse_relationships(transfer.get('relationships'))

        return ds.data_object_factory(
            type_,
            id_=transfer.get('id'),
            attributes=attributes,
            to_one=to_one,
            to_many=to_many,
        )

    def parse_stats(self, transfer: JsonApiResource) -> dict:
        type_ = transfer.get('type')
        raw_stats = transfer.get('stats')
        converted_stats = self.__convert_stats(type_, raw_stats)
        return {'stats': converted_stats}

    def parse_group_stats(self, transfer: JsonApiResource) -> Iterable[dict]:
        type_ = transfer.get('type')
        raw_stats = transfer.get('stats')

        return [self.__convert_group_stats(type_, raw_stat) for raw_stat in raw_stats]

    def __get_data_source(self, type_: str) -> DataSource:
        return self.__ds_dict[type_]

    def __parse_relationships(
        self, related: dict[str, JsonApiResource] | None
    ) -> tuple[dict[str, DataObject | None], dict[str, list[DataObject]]]:
        to_one = {}
        to_many = {}
        if related:
            for name, value in related.items():
                if value is None:
                    # This must be a to-one relation because to-many relations
                    # are never null.  (If the to-many has been fetched it
                    # will be an empty list. If it has not been fetched it
                    # will be a dict containing a "links" key.)
                    to_one[name] = None
                elif data := value.get('data'):
                    if isinstance(data, list):
                        to_many[name] = [self.__make_stub_data_object(x) for x in data]
                    else:
                        to_one[name] = None if data is None else self.__make_stub_data_object(data)
        return to_one, to_many

    def __make_stub_data_object(self, transfer: JsonApiResource):
        type_ = transfer['type']
        ds = self.__get_data_source(type_)
        return ds.data_object_factory(
            type_,
            id_=transfer['id'],
            stub=True,
        )

    def __convert_attributes(
        self, type_: str, attributes: dict[str, Any] | None
    ) -> dict[str, Any]:
        if not attributes:
            return {}

        datetime_keys = self.__get_datetime_keys(type_)

        return {
            k: (dateutil_parse(v) if k in datetime_keys and v is not None else v)
            for k, v in attributes.items()
        }

    def __convert_stats(self, type_: str, stats: dict[str, Any] | None) -> dict[str, Any]:
        # {'field': {'min': value, 'max': value}
        if not stats:
            return {}

        datetime_keys = self.__get_datetime_keys(type_)

        return {
            fieldname: {
                k: (
                    dateutil_parse(v, ignoretz=True)
                    if fieldname in datetime_keys and v is not None and k in ['min', 'max']
                    else v
                )
                for k, v in fieldstats.items()
            }
            for fieldname, fieldstats in stats.items()
        }

    def __convert_group_stats(
        self, type_: str, raw_stats: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        st = raw_stats.pop('stats')
        count = st.pop('count', None)

        raw_stats['stats'] = self.__convert_stats(type_, st)

        if count is not None:
            raw_stats['stats']['count'] = count

        return raw_stats

    def __get_datetime_keys(self, type_: str) -> set[str]:
        """
        Gets called on each object, which is somewhat inefficient.  Should be
        cached for each object type, but don't want `self` in a cache because
        it could leak memory.
        """
        ds = self.__get_data_source(type_)
        attribute_types = ds.attribute_types.get(type_, {})

        return {attr for attr, typ in attribute_types.items() if self.__type_is_datetime(typ)}

    def __type_is_datetime(self, typ: str, /) -> bool:
        lc_type = typ.lower()

        return 'date' in lc_type or 'time' in lc_type


class DataObjectCatalog:
    """
    A catalog of `DataObject`s keyed by their `type` and `id` attributes.
    """

    def __init__(self, data_obj_list: Iterable[DataObject] | None):
        self.__obj_index = {}
        if data_obj_list:
            for obj in data_obj_list:
                self.store(obj)

    def __len__(self):
        return len(self.__obj_index)

    def store(self, obj) -> None:
        key = obj.type, obj.id
        self.__obj_index[key] = obj

    def fetch(self, obj) -> DataObject | None:
        key = obj.type, obj.id
        return self.__obj_index.get(key)
