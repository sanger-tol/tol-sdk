# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Union

from ..core import DataObject
from ..core.operator import Relational
from ..core.relationship import RelationshipConfig


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

    def __init__(self, prefix: str = '') -> None:
        self.__prefix = prefix

    def dump(
        self,
        data_object: DataObject,
        document_meta: Optional[DocumentMeta] = None
    ) -> ResponseDict:
        response = {
            'data': self.__dump_object(data_object)
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
            self.__dump_object(data_object)
            for data_object in data_objects
        ]
        response = {
            'data': dumped
        }
        if document_meta is not None:
            response['meta'] = document_meta
        return response

    def __dump_object(self, data_object: DataObject) -> DumpDict:
        dump = {
            'type': data_object.type,
            'id': data_object.id
        }
        if data_object.attributes:
            dump['attributes'] = data_object.attributes
        dump = self.__add_relationships(data_object, dump)
        return dump

    def __add_relationships(
        self,
        data_object: DataObject,
        dump: DumpDict
    ) -> DumpDict:

        keys = self.__get_relationship_keys(data_object)
        if not keys:
            return dump
        dump['relationships'] = self.__get_relationship_dumps(
            keys,
            data_object.type,
            data_object.id
        )
        return dump

    def __get_relationship_dumps(
        self,
        relationships: list[str],
        type_: str,
        id_: str
    ) -> AllRelationshipsDump:

        return {
            key: self.__dump_relationship(key, type_, id_)
            for key in relationships
        }

    def __dump_relationship(
        self,
        key: str,
        type_: str,
        id_: str
    ) -> RelationshipDump:

        link = f'{self.__prefix}/{type_}/{id_}/{key}'
        return {
            'links': {
                'related': link
            }
        }

    def __get_relationship_keys(
        self,
        data_object: DataObject
    ) -> list[str]:

        host = data_object.host
        if not isinstance(host, Relational):
            return []
        return self.__get_keys_from_host(
            host,
            data_object.type
        )

    def __get_keys_from_host(
        self,
        host: Relational,
        type_: str
    ) -> list[str]:

        config = host.relationship_config.get(type_)
        if config is None:
            return []
        return self.__join_keys(config)

    def __join_keys(
        self,
        config: RelationshipConfig
    ) -> list[str]:

        return list(
            chain(
                self.__keys_or_empty(config.to_one),
                self.__keys_or_empty(config.to_many)
            )
        )

    def __keys_or_empty(
        self,
        config: Optional[dict[str, str]]
    ) -> Iterable[str]:

        return (
            config.keys() if config is not None else []
        )
