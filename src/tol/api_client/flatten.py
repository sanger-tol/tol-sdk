# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable, List
from uuid import uuid4

from ..core import DataObject


class Flattener:
    """
    Flattens a list of DataObject instances, containing nested relationship
    references, and assigns each a unique UUID.

    This UUID is used by a Dumper instance to identify the targets of
    relationships for DataObject instances.
    """

    def __init__(self) -> None:
        self.__processed_objects: List[DataObject] = []

    def flatten(self, objects: Iterable[DataObject]) -> List[DataObject]:
        for data_object in objects:
            self.__process_object(data_object)
        return self.__processed_objects

    def __process_object(self, data_object: DataObject) -> None:
        if self.__seen_already(data_object):
            return
        self.__record_object(data_object)
        self.__process_relationships(data_object)

    def __seen_already(self, data_object: DataObject) -> bool:
        return hasattr(data_object, '_request_uuid')

    def __record_object(self, data_object: DataObject) -> None:
        data_object._request_uuid = uuid4().hex
        self.__processed_objects.append(data_object)

    def __process_relationships(self, data_object: DataObject) -> None:
        self.__process_one_relationships(data_object)
        self.__process_many_relationships(data_object)

    def __process_one_relationships(self, data_object: DataObject) -> None:
        relationships = data_object.to_one_relationships
        for one_object in relationships.values():
            self.__process_object(one_object)

    def __process_many_relationships(self, data_object: DataObject) -> None:
        relationships = data_object.to_many_relationships
        for many_relationship in relationships.values():
            for many_object in many_relationship:
                self.__process_object(many_object)
