# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Protocol, Type

from .data_object import DataDict, DataObject
from .data_source_dict import DataSourceDict
from .relationship import (
    NotRelationalError,
    Relational,
    ToManyDict,
    ToOneDict
)

if typing.TYPE_CHECKING:
    from .datasource import DataSource


class DataObjectFactory(Protocol):
    """
    A factory that takes several args and kwargs, and returns
    a new DataObject instance.
    """

    def __call__(
        self,
        type_: str,
        id_: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> DataObject:
        ...


class CoreDataObject(DataObject, ABC):
    """
    A DataObject that can be created outside of a DataSource, which
    should prove sufficient for most use-cases. Simply set values
    on an instance, and they will be interpreted as either:

    - to-one relationships  - if the value is a single DataObject
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
        type_: str,
        data: Optional[DataDict] = None,
        id_: Optional[str] = None
    ):
        self.__id = id_
        self.__type = type_
        if data is not None:
            self.set_data(data)

    @property
    def type(self) -> str:  # noqa
        return self.__type

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
            if not self.__is_data_object(key)
        }

    @property
    def to_one_relationships(self) -> Dict[str, Optional[DataObject]]:
        if not self._relational:
            raise NotRelationalError(self)
        return ToOneDict(self, self._host)

    @property
    def to_many_relationships(self) -> Dict[str, Iterable[DataObject]]:
        if not self._relational:
            raise NotRelationalError(self)
        return ToManyDict(self, self._host)

    @property
    @abstractmethod
    def _host(self) -> DataSource:
        """
        The DataSource instance that manages DataObject instance of this type
        """

    @property
    def _to_one_objects(self) -> Dict[str, DataObject]:
        """The name: attribute mapping for DataObjects set on this instance"""

        field_names = self.__get_field_names()
        return {
            k: getattr(self, k) for k in field_names
            if self.__is_data_object(k)
        }

    @property
    def _relational(self) -> bool:
        """Whether the hosting DataSource is relational or not"""

        return isinstance(self._host, Relational)

    def __is_data_object(self, name: str) -> bool:
        value = getattr(self, name)
        return isinstance(value, DataObject)

    def __get_field_names(self) -> List[str]:
        return [
            v for v in vars(self)
            if not v.startswith('_')
            and v not in self.__NON_FIELD_NAMES
        ]


def core_data_object(*data_sources: DataSource) -> Type[CoreDataObject]:
    """
    Takes a tuple of DataSource instances, and creates a CoreDataObject
    implementation that refers to all of them.

    This must be called for the given DataSources to be able to create
    CoreDataObject instances (as it injects a factory).
    """

    data_source_dict = DataSourceDict(*data_sources)

    class DefaultCoreDataObject(CoreDataObject):
        """The default implementation of CoreDataObject"""

        @property
        def _host(self) -> DataSource:
            return data_source_dict[self.type]

    def core_data_object_factory(
        type_: str,
        id_: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> DataObject:

        return DefaultCoreDataObject(type_, id_=id_, data=data)

    for ds in data_sources:
        ds.data_object_factory = core_data_object_factory

    return DefaultCoreDataObject
