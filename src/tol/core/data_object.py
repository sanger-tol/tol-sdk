# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC
from collections.abc import Iterable as IterableABC
from typing import Any, Dict, Iterable


DataDict = Dict[str, Any]


class DataObject(ABC):
    """
    The abstract base class for the unit of data
    on which a DataSource operates.
    """

    def __init__(
        self,
        object_type: str,
        data: DataDict = None
    ):
        self.__set_non_attribute('_field_keys', set())
        self.__set_non_attribute('_object_type', object_type)
        if data is not None:
            self.set_data(data)

    @property
    def id(self) -> str:
        return getattr(self, '_id', None)

    @id.setter
    def set_id(self, id_) -> None:
        # this needs to both be settable externally _and_
        # bypass infinite recursion, like object_type
        self.__set_non_attribute('_id', id_)

    @property
    def object_type(self) -> str:
        return self._object_type

    def set_data(self, data: DataDict) -> None:
        """
        Sets the data as given to the constructor.
        Override for custom behaviour.
        """
        for key, value in data.items():
            setattr(self, key, value)

    @property
    def attributes(self) -> Dict[str, Any]:
        """
        The bare attributes (non-relationships) of this DataObject
        """
        return {
            key: getattr(self, key)
            for key in self._field_keys
            if self.__is_attribute(key)
        }

    @property
    def to_one_relationships(self) -> Dict[str, DataObject]:
        """
        The to-one relationships of this DataObject, i.e. the
        relationships for which this "points" at 1 single other
        DataObject
        """
        return {
            key: getattr(self, key)
            for key in self._field_keys
            if self.__is_to_one_relationship(key)
        }

    @property
    def to_many_relationships(self) -> Dict[str, Iterable[DataObject]]:
        """
        The to-many relationships of this DataObject, i.e. the
        relation DataObject instances that "point" to this instance
        """
        return {
            key: getattr(self, key)
            for key in self._field_keys
            if self.__is_to_many_relationship(key)
        }

    def __setattr__(self, name: str, value: Any) -> None:
        if name != 'id':
            self._field_keys.add(name)
            return super().__setattr__(name, value)
        object.__setattr__(self, '_id', value)

    def __set_non_attribute(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    def __is_attribute(self, name: str) -> bool:
        return (
            not self.__is_to_one_relationship(name)
            and not self.__is_to_many_relationship(name)
        )

    def __is_to_one_relationship(self, name: str) -> bool:
        value = getattr(self, name)
        return isinstance(value, DataObject)

    def __is_to_many_relationship(self, name: str) -> bool:
        value = getattr(self, name)
        return (
            isinstance(value, IterableABC)
            and not isinstance(value, str)
        )
