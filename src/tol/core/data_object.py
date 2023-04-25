# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractproperty
from collections.abc import Iterable as IterableABC
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4


DataDict = Dict[str, Any]


class DataObject(ABC):
    """
    The ABC for the unit of data on which a DataSource instance
    operates - representing the lingua franca of DataSource instances,
    and declaring all abstract properties that are needed.
    """

    @abstractproperty
    def type(self) -> str:  # noqa
        """
        The type of this object (e.g. species/specimens/samples).
        """

    @abstractproperty
    def id(self) -> Optional[str]:  # noqa
        """
        A unique ID by which to identify this object within
        its type.
        """

    @abstractproperty
    def attributes(self) -> Dict[str, Any]:
        """
        A dictionary of key:attribute pairs, where an attribute
        is any entry on the object that is none of an ID, type,
        or relationship.
        """

    @abstractproperty
    def to_one_relationships(self) -> Dict[str, DataObject]:
        """
        A dictionary of relationships, where this object refers to
        precisely one other.
        """

    @abstractproperty
    def to_many_relationships(self) -> Dict[str, List[DataObject]]:
        """
        A dictionary of relationships, where many objects refer to
        precisely this object.
        """

    @abstractproperty
    def _internal_uuid(self) -> str:
        """
        An internal UUID, serving to uniquely identify created objects
        where the ID is either unknown or unknowable at creation.
        """


class CoreDataObject(DataObject):
    """
    The core unit of data on which a DataSource operates, which
    should prove sufficient for most use-cases. Simply set values
    on an instance, and they will be interpreted as either:

    - to-one relationships  - if the value is a single DataObject
    - to-many relationships - if the value is any non-string Iterable
    - attributes            - otherwise

    Note there are other supported DataObject classes - any class
    that inherits from DataObject meets the criteria.
    """

    __NON_FIELD_NAMES = [
        'id',
        'type'
    ]

    def __init__(
        self,
        object_type: str,
        data: DataDict = None
    ):
        self.__id: str = None
        self.__object_type = object_type
        self.__internal_uuid = uuid4().hex
        if data is not None:
            self.set_data(data)

    @property
    def type(self) -> str:  # noqa
        return self.__object_type

    @property
    def id(self) -> Optional[str]:  # noqa
        return self.__id

    @id.setter
    def id(self, new_id: str) -> None:  # noqa
        self.__id = new_id

    def set_data(self, data: DataDict) -> None:
        """
        Sets the data as given to the constructor.
        Override for custom behaviour.
        """
        for key, value in data.items():
            setattr(self, key, value)

    @property
    def attributes(self) -> Dict[str, Any]:
        return {
            key: getattr(self, key)
            for key in self.__get_field_names()
            if self.__is_attribute(key)
        }

    @property
    def to_one_relationships(self) -> Dict[str, CoreDataObject]:
        return {
            key: getattr(self, key)
            for key in self.__get_field_names()
            if self.__is_to_one_relationship(key)
        }

    @property
    def to_many_relationships(self) -> Dict[str, Iterable[CoreDataObject]]:
        return {
            key: getattr(self, key)
            for key in self.__get_field_names()
            if self.__is_to_many_relationship(key)
        }

    @property
    def _internal_uuid(self) -> str:
        return self.__internal_uuid

    def __is_attribute(self, name: str) -> bool:
        return (
            not self.__is_to_one_relationship(name)
            and not self.__is_to_many_relationship(name)
        )

    def __is_to_one_relationship(self, name: str) -> bool:
        value = getattr(self, name)
        return isinstance(value, CoreDataObject)

    def __is_to_many_relationship(self, name: str) -> bool:
        value = getattr(self, name)
        return (
            isinstance(value, IterableABC)
            and not isinstance(value, str)
        )

    def __get_field_names(self) -> List[str]:
        return [
            v for v in vars(self)
            if not v.startswith('_')
            and v not in self.__NON_FIELD_NAMES
        ]
