# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import Any, Dict, List

from ..core import DataObject


class _ApiObjectSerializer:
    """
    Serializes an individual object (Private API)
    """
    def __init__(self):
        self.__dumped = {}

    def dump(self, data_object: DataObject) -> Dict[str, Any]:
        self.__data_object = data_object
        self.__add_mandatory_fields()
        self.__add_optional_fields()
        self.__add_relationships()
        return self.__dumped

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

    def __add_to_many_relationship(
        self,
        key: str,
        data_objects: List[DataObject]
    ) -> None:
        to_many_uuids = [
            d._request_internal_uuid for d in data_objects
        ]
        self.__dumped['relationships']['many'][key] = to_many_uuids

    def __add_to_many_relationships(self) -> None:
        to_many = self.__data_object.to_many_relationships
        if not to_many:
            return
        self.__dumped['relationships']['many'] = {}
        for key, data_objects in to_many:
            self.__add_to_many_relationship(key, data_objects)

    def __add_optional_fields(self) -> None:
        if self.__data_object.id is not None:
            self.__dumped['id'] = self.__data_object.id
        if self.__data_object.attributes:
            self.__dumped['attributes'] = self.__data_object.attributes


class ApiDataSerializer:
    """
    Serializes a complex, nested List of DataObjects into
    a flat list of raw data.
    """

    def __init__(self):
        self.__uuid_dump_map: Dict[str, Dict[str, Any]] = {}

    def dump(self, data_objects: List[DataObject]) -> List[Dict[str, Any]]:
        self.__data_objects = data_objects
