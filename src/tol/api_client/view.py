# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import urllib
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Union

from ..core import DataObject
from ..core.operator import Relational

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
        document_meta: Optional[DocumentMeta] = None
    ) -> ResponseDict:
        """
        Create a JSON:API response for an individual DataObject result
        """

    @abstractmethod
    def dump_bulk(
        self,
        data_objects: Iterable[DataObject],
        document_meta: Optional[DocumentMeta] = None
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
        prefix: str = '',
        include_all_to_ones: bool = False,
        hop_limit: Optional[int] = None,
        requested_fields: list[str] | None = None,
    ) -> None:
        """
        Args:

        - prefix                - the URL prefix on which the
                                  data blueprint is served
        - include_all_to_ones   - whether to fetch all absent
                                  to-one relation objects,
                                  using the "host" `Relational`
                                  instance
        - hop_limit             - the maximum recursion limit
                                  on including related to-one
                                  objects. Default no limit
        """

        self.__prefix = prefix
        self.__all_to_ones = include_all_to_ones
        self.__hop_limit = hop_limit
        self.__requested_fields = requested_fields

    def dump(
        self,
        data_object: DataObject,
        document_meta: Optional[DocumentMeta] = None
    ) -> ResponseDict:

        response = {
            'data': self.__dump_object(
                data_object,
                self.__initial_marker,
            )
        }
        if document_meta is not None:
            response['meta'] = document_meta
        return response

    def dump_bulk(
        self,
        data_objects: Iterable[DataObject],
        document_meta: Optional[DocumentMeta] = None
    ) -> ResponseDict:

        dumped = [
            self.__dump_object(
                data_object,
                self.__initial_marker,
            )
            for data_object in data_objects
        ]
        response = {
            'data': dumped
        }
        if document_meta is not None:
            response['meta'] = document_meta
        return response

    @property
    def __initial_marker(self) -> int | str:
        if self.__requested_fields:
            return ''
        else:
            return 0

    def __dump_object(
        self,
        data_object: DataObject,
        marker: int | str,
    ) -> DumpDict:

        dump = {
            'type': data_object.type,
            'id': data_object.id
        }
        if data_object.attributes:
            dump['attributes'] = self.__convert_attributes(
                data_object.attributes
            )
        dump = self.__add_relationships(data_object, dump, marker)
        return dump

    def __add_relationships(
        self,
        data_object: DataObject,
        dump: DumpDict,
        marker: int
    ) -> DumpDict:

        host = data_object._host
        if not isinstance(host, Relational):
            return dump

        to_one_keys = self.__get_to_one_keys(data_object)
        to_many_keys = self.__get_to_many_keys(host, data_object.type)
        if not to_one_keys and not to_many_keys:
            return dump
        dump['relationships'] = self.__get_relationship_dumps(
            to_one_keys,
            to_many_keys,
            data_object,
            marker
        )
        return dump

    def __get_relationship_dumps(
        self,
        to_one_relationships: list[str],
        to_many_relationships: list[str],
        data_object: DataObject,
        marker: int
    ) -> AllRelationshipsDump:

        dump = {
            key: self.__dump_to_one_relationship(key, data_object, marker)
            for key in to_one_relationships
        } | {
            key: self.__dump_to_many_relationship(key, data_object.type,
                                                  data_object.id)
            for key in to_many_relationships
        }

        return {
            k: v for k, v in dump.items() if v != {}
        }

    def __dump_to_many_relationship(
        self,
        key: str,
        type_: str,
        id_: str
    ) -> RelationshipDump:

        id_encoded = urllib.parse.quote(str(id_), safe='')
        link = f'{self.__prefix}/{type_}/{id_encoded}/{key}'
        return {
            'links': {
                'related': link
            }
        }

    def __dump_to_one_relationship(
        self,
        key: str,
        data_object: DataObject,
        marker: int | str
    ) -> Optional[RelationshipDump]:

        if self.__hop_limit is not None and marker >= self.__hop_limit:
            return {}

        if self.__requested_fields and not self.__to_one_is_relevant(key, marker):
            return {}

        related_object = self.__get_related_to_one(data_object, key)
        if related_object is not None:
            next_marker = self.__get_next_marker(marker, key)
            return {
                'data': self.__dump_object(
                    related_object,
                    next_marker,
                )
            }

    def __get_next_marker(
        self,
        marker: int | str,
        key: str,
    ) -> int | str:

        return (
            (f'{marker}.{key}' if marker else key)
            if self.__requested_fields
            else marker + 1
        )

    def __to_one_is_relevant(
        self,
        key: str,
        marker: str
    ) -> bool:

        next_marker = self.__get_next_marker(marker, key)

        return any(
            r for r in self.__requested_fields
            if r.startswith(next_marker)
        )

    def __get_related_to_one(
        self,
        data_object: DataObject,
        key: str
    ) -> Optional[DataObject]:

        relations = (
            data_object.to_one_relationships
            if self.__all_to_ones
            else data_object._to_one_objects
        )
        return relations.get(key)

    def __get_to_one_keys(
        self,
        obj: DataObject
    ) -> list[str]:

        if self.__all_to_ones:
            return self.__get_target_keys(
                obj._host,
                obj.type,
                'to_one'
            )
        else:
            return list(
                obj._to_one_objects.keys()
            )

    def __get_to_many_keys(
        self,
        host: Relational,
        type_: str
    ) -> list[str]:

        return self.__get_target_keys(host, type_, 'to_many')

    def __get_target_keys(
        self,
        host: Relational,
        type_: str,
        target_name: str
    ) -> list[str]:

        if host.relationship_config is None:
            return []
        config = host.relationship_config.get(type_)
        if config is None:
            return []
        target = getattr(config, target_name)
        return self.__keys_or_empty(target)

    def __keys_or_empty(
        self,
        config: Optional[dict[str, str]]
    ) -> Iterable[str]:

        return (
            config.keys() if config is not None else []
        )

    def __convert_attributes(
        self,
        attributes: dict[str, Any]
    ) -> dict[str, Any]:

        return {
            k: self.__convert_value(v)
            for k, v in attributes.items()
        }

    def __convert_value(self, __v: Any) -> Any:
        if isinstance(__v, (date, datetime)):
            return __v.isoformat()
        return __v
