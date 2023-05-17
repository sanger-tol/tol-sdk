# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterable, List, Union

from ..core import DataObject


DumpedObject = Dict[str, Any]
UpsertDump = Dict[str, Union[List[DumpedObject], Any]]


class ObjectDumper(ABC):
    """
    The ABC for dumping an individual instance of DataObject.

    The given DataObject instance must have been tagged, by
    setting a (request-internal) attribute `_request_uuid`
    """

    @abstractmethod
    def dump(self, data_object: DataObject) -> DumpedObject:
        """Dump the provided DataObject instance"""


ObjectDumperFactory = Callable[[], ObjectDumper]


class DefaultObjectDumper(ObjectDumper):
    """
    A reasonable, default implementation of the ObjectDumper ABC.
    """

    def __init__(self) -> None:
        self.__dumped: DumpedObject = {}

    def dump(self, data_object: DataObject) -> DumpedObject:
        self.__data_object = data_object
        self.__add_fields()
        return self.__dumped

    def __add_fields(self) -> None:
        self.__add_mandatory_fields()
        self.__add_optional_fields()
        self.__add_relationships()

    def __add_mandatory_fields(self) -> None:
        self.__dumped['type'] = self.__data_object.type
        self.__dumped['_uuid'] = self.__data_object._request_uuid

    def __add_optional_fields(self) -> None:
        if self.__data_object.id is not None:
            self.__dumped['id'] = self.__data_object.id
        if self.__data_object.attributes:
            self.__dumped['attributes'] = self.__data_object.attributes

    def __add_relationships(self) -> None:
        if self.__no_relationships():
            return
        self.__dumped['relationships'] = {}
        self.__add_to_one_relationships()
        self.__add_to_many_relationships()

    def __no_relationships(self) -> None:
        d = self.__data_object
        return not (d.to_one_relationships or d.to_many_relationships)

    def __add_to_one_relationships(self) -> None:
        ones = self.__data_object.to_one_relationships
        if not ones:
            return
        self.__dumped['relationships']['one'] = {
            key: o._request_uuid
            for key, o in ones.items()
        }

    def __add_to_many_relationships(self) -> None:
        manys = self.__data_object.to_many_relationships
        if not manys:
            return
        self.__dumped['relationships']['many'] = {
            key: self.__format_many_objects(many_objects)
            for key, many_objects
            in manys.items()
        }

    def __format_many_objects(
        self,
        many_objects: Iterable[DataObject]
    ) -> None:
        return [
            m._request_uuid for m in many_objects
        ]


class UpsertDumper:
    """
    Dumps an Iterable of DataObject instances that have been:

    - flattened - every object is included at the top-level,
                  regardless of any other nesting
    - tagged    - every object has been assigned a UUID hex string

    Uses the given factory method that returns a new ObjectDumper
    instance on each invocation.
    """

    def __init__(self, object_dumper_factory: ObjectDumperFactory) -> None:
        self.__object_dumper_factory = object_dumper_factory

    def dump(self, objects: Iterable[DataObject]) -> UpsertDump:
        """
        Dumps an iterable of DataObject instances to a python dictionary.
        """
        sorted_objects = sorted(
            objects,
            key=lambda d: d.type
        )
        dumped_objects = [
            self.__object_dumper_factory().dump(data_object)
            for data_object in sorted_objects
        ]
        return {
            'data': dumped_objects
        }
