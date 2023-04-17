# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Dict, List

from .api_data_object import ApiResponseDataObject


class ApiObjectSerializer:
    """
    Serializes an individual object (Private API)
    """
    def __init__(self):
        self.__dumped: Dict[str, Any] = {}

    def dump(self, data_object: ApiResponseDataObject) -> Dict[str, Any]:
        self.__data_object = data_object
        self.__create_dump()
        return self.__dumped

    def __create_dump(self) -> None:
        self.__add_mandatory_fields()
        self.__add_optional_fields()
        self.__add_relationships()

    def __add_mandatory_fields(self) -> None:
        self.__dumped['type'] = self.__data_object.object_type
        self.__dumped['_uuid'] = self.__data_object._request_internal_uuid

    def __add_relationships(self) -> None:
        if not (
            self.__data_object.to_one_relationships
            or self.__data_object.to_many_relationships
        ):
            return
        self.__dumped['relationships'] = {}
        self.__add_to_one_relationships()
        self.__add_to_many_relationships()

    def __add_to_one_relationships(self) -> None:
        if not self.__data_object.to_one_relationships:
            return
        to_one_uuids = {
            k: d._request_internal_uuid
            for k, d in self.__data_object.to_one_relationships.items()
        }
        self.__dumped['relationships']['one'] = to_one_uuids

    def __get_to_many_relationship_uuids(
        self,
        data_objects: List[ApiResponseDataObject]
    ) -> List[str]:
        return [
            d._request_internal_uuid for d in data_objects
        ]

    def __add_to_many_relationships(self) -> None:
        to_many = self.__data_object.to_many_relationships
        if not to_many:
            return
        self.__dumped['relationships']['many'] = {
            key: self.__get_to_many_relationship_uuids(data_objects)
            for key, data_objects in to_many.items()
        }

    def __add_optional_fields(self) -> None:
        if self.__data_object.id is not None:
            self.__dumped['id'] = self.__data_object.id
        if self.__data_object.attributes:
            self.__dumped['attributes'] = self.__data_object.attributes


class ApiDataSerializer:
    """
    Serializes a complex, nested List of ApiDataObjects into
    a flat list of raw data, ready for an upsert operation.
    """

    def __init__(self):
        # store against _request_internal_uuid so that duplicates are
        # removed
        self.__uuid_dump_map: Dict[str, Dict[str, Any]] = {}

    def dump(self, data_objects: List[ApiResponseDataObject]) -> List[Dict[str, Any]]:
        self.__flatten_dump_add(data_objects)
        return self.__get_serialized_list()

    def __flatten_dump_add(self, data_objects: List[ApiResponseDataObject]) -> None:
        for data_object in data_objects:
            if self.__object_already_processed(data_object):
                continue
            self.__add_data_object(data_object)
            self.__add_to_one_relationships(data_object)
            self.__add_to_many_relationships(data_object)

    def __object_already_processed(self, data_object: ApiResponseDataObject) -> bool:
        return data_object._request_internal_uuid in self.__uuid_dump_map

    def __add_to_one_relationships(
        self,
        data_object: ApiResponseDataObject
    ) -> None:
        for to_one_relation in data_object.to_one_relationships.values():
            self.__flatten_dump_add([to_one_relation])

    def __add_to_many_relationships(
        self,
        data_object: ApiResponseDataObject
    ) -> None:
        for to_many_relations in data_object.to_many_relationships.values():
            self.__flatten_dump_add(to_many_relations)

    def __add_data_object(self, data_object: ApiResponseDataObject) -> None:
        uuid = data_object._request_internal_uuid
        dumped = ApiObjectSerializer().dump(data_object)
        self.__uuid_dump_map[uuid] = dumped

    def __get_serialized_list(self) -> List[Dict[str, Any]]:
        unsorted = self.__uuid_dump_map.values()
        return sorted(
            unsorted,
            key=lambda d: d['type']
        )
