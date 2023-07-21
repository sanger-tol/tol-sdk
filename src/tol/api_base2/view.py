# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import urllib
from abc import ABC, abstractmethod
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Union

from ..core import DataObject
from ..core.operator import Relational
<<<<<<< HEAD
=======
from ..core.relationship import RelationshipConfig
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)


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

<<<<<<< HEAD
        to_one_keys = self.__get_to_one_relationship_keys(data_object)
        to_many_keys = self.__get_to_many_relationship_keys(data_object)
        if not to_one_keys and not to_many_keys:
            return dump
        dump['relationships'] = self.__get_relationship_dumps(
            to_one_keys,
            to_many_keys,
            data_object
=======
        keys = self.__get_relationship_keys(data_object)
        if not keys:
            return dump
        dump['relationships'] = self.__get_relationship_dumps(
            keys,
            data_object.type,
            data_object.id
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)
        )
        return dump

    def __get_relationship_dumps(
        self,
<<<<<<< HEAD
        to_one_relationships: list[str],
        to_many_relationships: list[str],
        data_object: DataObject
    ) -> AllRelationshipsDump:

        return {
            key: self.__dump_to_one_relationship(key, data_object)
            for key in to_one_relationships
        } | {
            key: self.__dump_to_many_relationship(key, data_object.type,
                                                  data_object.id)
            for key in to_many_relationships
        }

    def __dump_to_many_relationship(
=======
        relationships: list[str],
        type_: str,
        id_: str
    ) -> AllRelationshipsDump:

        return {
            key: self.__dump_relationship(key, type_, id_)
            for key in relationships
        }

    def __dump_relationship(
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)
        self,
        key: str,
        type_: str,
        id_: str
    ) -> RelationshipDump:
<<<<<<< HEAD
        id_encoded = urllib.parse.quote(id_, safe='')
        link = f'{self.__prefix}/{type_}/{id_encoded}/{key}'
=======

        link = f'{self.__prefix}/{type_}/{id_}/{key}'
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)
        return {
            'links': {
                'related': link
            }
        }

<<<<<<< HEAD
    def __dump_to_one_relationship(
        self,
        key: str,
        data_object: DataObject
    ) -> RelationshipDump:
        related_object = data_object.host.get_to_one_relation(data_object, key)
        if related_object is not None:
            return {
                'data': {
                    'type': data_object.host.relationship_config[data_object.type].to_one[key],
                    'id': related_object.id,
                    'attributes': related_object.attributes
                }
            }
        return {}

    def __get_to_one_relationship_keys(
=======
    def __get_relationship_keys(
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)
        self,
        data_object: DataObject
    ) -> list[str]:

        host = data_object.host
        if not isinstance(host, Relational):
            return []
<<<<<<< HEAD
        return self.__get_to_one_keys_from_host(
=======
        return self.__get_keys_from_host(
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)
            host,
            data_object.type
        )

<<<<<<< HEAD
    def __get_to_many_relationship_keys(
        self,
        data_object: DataObject
    ) -> list[str]:

        host = data_object.host
        if not isinstance(host, Relational):
            return []
        return self.__get_to_many_keys_from_host(
            host,
            data_object.type
        )

    def __get_to_one_keys_from_host(
=======
    def __get_keys_from_host(
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)
        self,
        host: Relational,
        type_: str
    ) -> list[str]:

<<<<<<< HEAD
        if host.relationship_config is None:
            return []
        config = host.relationship_config.get(type_)
        if config is None:
            return []
        return self.__keys_or_empty(config.to_one)

    def __get_to_many_keys_from_host(
        self,
        host: Relational,
        type_: str
    ) -> list[str]:

        if host.relationship_config is None:
            return []
        config = host.relationship_config.get(type_)
        if config is None:
            return []
        return self.__keys_or_empty(config.to_many)
=======
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
>>>>>>> 834d922 (TOLP-6088 Add relationships to DefaultView dump methods)

    def __keys_or_empty(
        self,
        config: Optional[dict[str, str]]
    ) -> Iterable[str]:

        return (
            config.keys() if config is not None else []
        )
