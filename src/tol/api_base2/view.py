# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import urllib
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Union

from flask import make_response

from tol.excel import convert_data_objects_to_excel

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

    @abstractmethod
    def dump_bulk_excel(
        self,
        data_objects: Iterable[DataObject]
    ) -> ResponseDict:
        """
        Create an vnd.ms-excel response for an Iterable of DataObject results
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

    def dump_bulk_excel(
            self,
            data_objects: Iterable[DataObject],
            body: object
    ) -> ResponseDict:
        output_stream = convert_data_objects_to_excel(data_objects, body, 'Sheet1')
        response = make_response(output_stream.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=download_table.xlsx'
        response.headers['Content-type'] = 'application/vnd.ms-excel'
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

        to_one_keys = self.__get_to_one_relationship_keys(data_object)
        to_many_keys = self.__get_to_many_relationship_keys(data_object)
        if not to_one_keys and not to_many_keys:
            return dump
        dump['relationships'] = self.__get_relationship_dumps(
            to_one_keys,
            to_many_keys,
            data_object
        )
        return dump

    def __get_relationship_dumps(
        self,
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
        self,
        key: str,
        type_: str,
        id_: str
    ) -> RelationshipDump:
        id_encoded = urllib.parse.quote(id_, safe='')
        link = f'{self.__prefix}/{type_}/{id_encoded}/{key}'
        return {
            'links': {
                'related': link
            }
        }

    def __dump_to_one_relationship(
        self,
        key: str,
        data_object: DataObject
    ) -> RelationshipDump:
        related_object = data_object._host.get_to_one_relation(data_object, key)
        if related_object is not None:
            return {
                'data': {
                    'type': data_object._host.relationship_config[data_object.type].to_one[key],
                    'id': related_object.id,
                    'attributes': related_object.attributes
                }
            }
        return {}

    def __get_to_one_relationship_keys(
        self,
        data_object: DataObject
    ) -> list[str]:

        host = data_object._host
        if not isinstance(host, Relational):
            return []
        return self.__get_to_one_keys_from_host(
            host,
            data_object.type
        )

    def __get_to_many_relationship_keys(
        self,
        data_object: DataObject
    ) -> list[str]:

        host = data_object._host
        if not isinstance(host, Relational):
            return []
        return self.__get_to_many_keys_from_host(
            host,
            data_object.type
        )

    def __get_to_one_keys_from_host(
        self,
        host: Relational,
        type_: str
    ) -> list[str]:

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

    def __keys_or_empty(
        self,
        config: Optional[dict[str, str]]
    ) -> Iterable[str]:

        return (
            config.keys() if config is not None else []
        )
