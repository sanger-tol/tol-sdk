# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import urllib
from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Union

from ..core import DataObject
from ..core.requested_fields import ReqFieldsTree

DocumentMeta = Dict[str, Any]
DumpDict = Dict[str, Any]
DumpDictMany = List[DumpDict]
ResponseDict = Dict[str, Union[DumpDict, DumpDictMany]]


class View(ABC):
    """
    Provides an MVC-esque View class. Can serialize both an individual
    DataObject, as well as an Iterable of DataObject instances.
    """

    @abstractmethod
    def dump(
        self,
        data_object: DataObject,
        document_meta: Optional[DocumentMeta] = None,
    ) -> ResponseDict:
        """
        Create a JSON:API response for an individual DataObject result
        """

    @abstractmethod
    def dump_bulk(
        self,
        data_objects: Iterable[DataObject],
        document_meta: Optional[DocumentMeta] = None,
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
        hop_limit: Optional[int] = None,
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
        document_meta: Optional[DocumentMeta] = None,
    ) -> ResponseDict:
        response = {
            'data': self.__dump_object(
                data_object,
                tree=self.__requested_tree,
            ),
        }
        if document_meta is not None:
            response['meta'] = document_meta
        return response

    def dump_bulk(
        self,
        data_objects: Iterable[DataObject],
        document_meta: Optional[DocumentMeta] = None,
    ) -> ResponseDict:
        dumped = [
            self.__dump_object(
                data_object,
                tree=self.__requested_tree,
            )
            for data_object in data_objects
        ]
        response = {'data': dumped}
        if document_meta is not None:
            response['meta'] = document_meta
        return response

    def __dump_object(
        self,
        data_object: DataObject,
        tree: ReqFieldsTree,
    ) -> DumpDict:
        dump = {'type': data_object.type, 'id': data_object.id}
        # Stub trees are created by requested_fields paths ending in ".id"
        if not tree.is_stub:
            self.__add_attributes(data_object, dump, tree)
        if tree.has_relationships:
            self.__add_relationships(data_object, dump, tree)
        return dump

    def __add_attributes(
        self,
        data_object: DataObject,
        dump: DumpDict,
        tree: ReqFieldsTree | None,
    ):
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
        tree: ReqFieldsTree | None = None,
    ) -> DumpDict:
        rel_dict = self.__dump_to_one_relationships(
            data_object, tree
        ) | self.__dump_to_many_relationships(data_object, tree)
        if rel_dict:
            dump['relationships'] = rel_dict

    def __dump_to_one_relationships(
        self,
        data_object: DataObject,
        tree: ReqFieldsTree,
    ) -> RelationshipDump:
        to_ones = {}
        for name in tree.to_one_names():
            if name in data_object._to_one_objects:
                one_dump = None
                if one := data_object._to_one_objects.get(name):
                    if sub_tree := tree.get_sub_tree(name):
                        one_dump = {'data': self.__dump_object(one, tree=sub_tree)}
                    else:
                        one_dump = {'data': {'type': one.type, 'id': one.id}}
                to_ones[name] = one_dump
        return to_ones

    def __dump_to_many_relationships(
        self,
        data_object: DataObject,
        tree: ReqFieldsTree,
    ) -> RelationshipDump:
        quoted_id = urllib.parse.quote(str(data_object.id), safe='')
        to_many = {}
        for name in tree.to_many_names():
            if sub_tree := tree.get_sub_tree(name):
                to_many[name] = {
                    'data': [
                        self.__dump_object(x, tree=sub_tree) for x in getattr(data_object, name)
                    ]
                }
            else:
                link = f'{self.__prefix}/{data_object.type}/{quoted_id}/{name}'
                to_many[name] = {'links': {'related': link}}
        return to_many

    def __convert_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        return {k: self.__convert_value(v) for k, v in attributes.items()}

    def __convert_value(self, __v: Any) -> Any:
        if isinstance(__v, date):
            # `datetime` is a subclass of `date`
            return __v.isoformat()
        return __v
