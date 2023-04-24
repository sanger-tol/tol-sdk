# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractproperty
from collections.abc import Iterable as IterableABC
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4


DataDict = Dict[str, Any]


class DataObjectABC(ABC):
    @abstractproperty
    def type(self) -> str:  # noqa
        pass

    @abstractproperty
    def id(self) -> Optional[str]:  # noqa
        pass

    @abstractproperty
    def attributes(self) -> Dict[str, Any]:
        pass

    @abstractproperty
    def to_one_relationships(self) -> Dict[str, DataObjectABC]:
        pass

    @abstractproperty
    def to_many_relationships(self) -> Dict[str, List[DataObjectABC]]:
        pass

    @abstractproperty
    def _internal_uuid(self) -> str:
        pass


class DataObject(DataObjectABC):
    """
    The unit of data on which a DataSource operates.
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
    def id(self) -> str:  # noqa
        return self.__id

    @id.setter
    def id(self, __new_id: str) -> None:
        self.__id = __new_id

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
            for key in self.__get_field_names()
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
            for key in self.__get_field_names()
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
            for key in self.__get_field_names()
            if self.__is_to_many_relationship(key)
        }

    @property
    def _internal_uuid(self) -> str:
        """
        A UUID for references by other DataObject instances, when
        formatted as a flat list of DataObject dumps in an upsert
        request.
        """
        return self.__internal_uuid

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

    def __get_field_names(self) -> List[str]:
        return [
            v for v in vars(self)
            if not v.startswith('_')
            and v not in self.__NON_FIELD_NAMES
        ]
