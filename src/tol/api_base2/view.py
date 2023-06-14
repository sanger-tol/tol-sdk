# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Union

from ..core import DataObject


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


class DefaultView(View):
    """
    Provides a default implementation of the View ABC.
    """

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
        dump = self.__add_relationships(dump)
        return dump

    def __add_relationships(self, dump: DumpDict) -> DumpDict:
        # TODO implement this!!!
        # TODO if there are lots of objects, add caching!!!
        return dump
