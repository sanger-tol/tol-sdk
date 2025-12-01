# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import urllib
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import date
from typing import Any

from ..core import DataObject
from ..core.requested_fields import ReqFieldsTree

DocumentMeta = dict[str, Any]
DumpDict = dict[str, Any]
DumpDictMany = list[DumpDict]
ResponseDict = dict[str, DumpDict | DumpDictMany]


class View(ABC):
    """
    Provides an MVC-esque View class. Can serialize both an individual
    DataObject, as well as an Iterable of DataObject instances.
    """

    @abstractmethod
    def dump(
        self,
        data_object: DataObject,
        document_meta: DocumentMeta | None = None,
    ) -> ResponseDict:
        """
        Create a JSON:API response for an individual DataObject result
        """

    @abstractmethod
    def dump_bulk(
        self,
        data_objects: Iterable[DataObject],
        document_meta: DocumentMeta | None = None,
    ) -> ResponseDict:
        """
        Create a JSON:API response for an Iterable of DataObject results
        """


RelationshipDump = dict[str, dict[str, str]]
AllRelationshipsDump = dict[str, RelationshipDump]


class DefaultView(View):
    """
    Provides a default implementation of the View ABC.
    """

    def __init__(
        self,
        requested_tree: ReqFieldsTree,
        prefix: str = '',
        hop_limit: int | None = None,
    ) -> None:
        """
        Args:

        - prefix                - the URL prefix on which the
                                  data blueprint is served
        - hop_limit             - the maximum recursion limit
                                  on including related to-one
                                  objects. Default no limit
        - requested_tree        - a tree data structure of the
                                  requested fields for the query
        """

        self.__prefix = prefix
        self.__hop_limit = hop_limit
        self.__requested_tree = requested_tree

    def dump(
        self,
        data_object: DataObject,
        document_meta: DocumentMeta | None = None,
    ) -> ResponseDict:
        included = IncludedDumps()
        dumped = self.__dump_object(
            data_object,
            included,
            tree=self.__requested_tree,
        )
        response = {'data': dumped}
        if included:
            response['included'] = included.as_list()
        if document_meta is not None:
            response['meta'] = document_meta
        return response

    def dump_bulk(
        self,
        data_objects: Iterable[DataObject],
        document_meta: DocumentMeta | None = None,
    ) -> ResponseDict:
        included = IncludedDumps()
        dumped = [
            self.__dump_object(
                data_object,
                included,
                tree=self.__requested_tree,
            )
            for data_object in data_objects
        ]
        response = {'data': dumped}
        if included:
            response['included'] = included.as_list()
        if document_meta is not None:
            response['meta'] = document_meta
        return response

    def __dump_object(
        self,
        data_object: DataObject,
        included: IncludedDumps,
        tree: ReqFieldsTree,
    ) -> DumpDict:
        """
        Returns a JSON:API resource object for the `data_object`, recursively
        adding related objects as specified in the `tree: ReqFieldsTree`
        argument.  Related objects are accumulated in the `incldued` array.
        """
        dump = {'type': data_object.type, 'id': null_or_str(data_object.id)}
        # Stub trees are created by requested_fields paths ending in ".id"
        if not tree.is_stub:
            self.__add_attributes(data_object, dump, tree)
        if tree.has_relationships:
            self.__add_relationships(data_object, dump, included, tree)
        return dump

    def __add_attributes(
        self,
        data_object: DataObject,
        dump: DumpDict,
        tree: ReqFieldsTree | None,
    ):
        """
        If attributes are specified in the `tree: ReqFieldsTree`, adds only
        those to the dump.  Default is to add all attribtues.
        """
        if tree and (attr_names := tree.attribute_names):
            # Only add requested attributes
            dump['attributes'] = self.__convert_attributes(
                {name: getattr(data_object, name) for name in attr_names}
            )
        elif data_object.attributes:
            # Default behaviour is to add all attributes
            dump['attributes'] = self.__convert_attributes(data_object.attributes)

    def __add_relationships(
        self,
        data_object: DataObject,
        dump: DumpDict,
        included: IncludedDumps,
        tree: ReqFieldsTree | None = None,
    ) -> DumpDict:
        rel_dict = self.__dump_to_one_relationships(
            data_object, included, tree
        ) | self.__dump_to_many_relationships(data_object, included, tree)
        if rel_dict:
            dump['relationships'] = rel_dict

    def __dump_to_one_relationships(
        self,
        data_object: DataObject,
        included: IncludedDumps,
        tree: ReqFieldsTree,
    ) -> RelationshipDump:
        to_ones = {}
        for rel in tree.to_one_names():
            if rel in data_object._to_one_objects:
                one_dump = None
                if one := data_object._to_one_objects.get(rel):
                    one_dump = {'data': self.__dump_stub(one, rel)}
                    if sub_tree := tree.get_sub_tree(rel):
                        included.add_dump(self.__dump_object(one, included, tree=sub_tree))
                to_ones[rel] = one_dump
        return to_ones

    def __dump_to_many_relationships(
        self,
        data_object: DataObject,
        included: IncludedDumps,
        tree: ReqFieldsTree,
    ) -> RelationshipDump:
        oid = data_object.id
        quoted_id = None if oid is None else urllib.parse.quote(str(oid), safe='')
        to_many = {}
        for rel in tree.to_many_names():
            sub_tree = tree.get_sub_tree(rel)
            if sub_tree and rel in data_object._to_many_objects:
                many_obj = data_object._to_many_objects.get(rel)
                to_many[rel] = [self.__dump_stub(x, rel) for x in many_obj]
                for obj in many_obj:
                    included.add_dump(self.__dump_object(obj, included, sub_tree))
            elif quoted_id:
                link = f'{self.__prefix}/{data_object.type}/{quoted_id}/{rel}'
                to_many[rel] = {'links': {'related': link}}
        return to_many

    def __dump_stub(self, obj: DataObject, rel_name: str) -> dict[str, str]:
        """
        Create a stub JSON:API object, known in the JSON:API spec as
        a "resource identifier object".  Contains a sanity check for the `id`
        attribute having a value.  If we want to support, for example,
        storing related objects with auto-incremented IDs, we will need to
        implement creating `lid` local IDs for linking to resource objects in
        the `included` array.
        """
        if obj.id is None:
            msg = (
                f"Cannot serialise '{obj.type}' object in relation"
                f" '{rel_name}' because it has no `id` attribute"
            )
            raise ValueError(msg)
        return {'type': obj.type, 'id': str(obj.id)}

    def __convert_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return {k: self.__convert_value(v) for k, v in attributes.items()}

    def __convert_value(self, val: Any, /) -> Any:
        if isinstance(val, date):
            # `datetime` is a subclass of `date`
            return val.isoformat()
        return val


def null_or_str(oid: Any, /):
    """
    Return `oid` as a string if it isn't `None`
    """
    return None if oid is None else str(oid)


class IncludedDumps:
    """
    Maintains objects to be returned in the JSON:API `included` list, indexed
    by tuples of `(type, id)`.
    """

    def __init__(self):
        self.__type_id: dict[tuple[str, str], DumpDict] = {}

    def __len__(self):
        """
        Implemented so that an `IncludedDumps` object returns true in boolean
        context when it has entries.
        """
        return len(self.__type_id)

    def as_list(self):
        return list(self.__type_id.values())

    def add_dump(self, dump: DumpDict):
        """
        Add a new DumpDict to the collection.
        """
        key = dump['type'], dump['id']
        if key not in self.__type_id:
            self.__type_id[key] = dump
