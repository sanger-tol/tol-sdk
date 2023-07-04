# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Protocol,
    Type
)

from .data_object import DataDict, DataObject
from .data_source_dict import DataSourceDict
from .datasource_error import NotRelationalError
from .operator import Relational
from .relationship import ToManyDict, ToOneDict

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


class DataSourceDictFactory(Protocol):
    """
    A factory that takes a variable number of `DataSource` instances,
    and returns a `dict` mapping `DataObject` type to its hosting
    `DataSource`.
    """

    def __call__(
        self,
        *data_sources: DataSource
    ) -> dict[str, DataSource]:
        ...


OneDictFactory = Callable[
    [DataObject],
    Dict[str, Optional[DataObject]]
]
"""
Takes a `DataObject` instance, returns a `dict` mapping
to-one relationship names to its `Optional[DataObject]`
"""


ManyDictFactory = Callable[
    [DataObject],
    Dict[str, Iterable[DataObject]]
]
"""
Takes a `DataObject` instance, returns a `dict` mapping
to-many relationship names to its `Iterable[DataObject]`
"""


def core_data_object(
    *data_sources: DataSource,
    one_dict_factory: OneDictFactory = lambda o: ToOneDict(o),
    many_dict_factory: ManyDictFactory = lambda o: ToManyDict(o),
    data_source_dict_factory: DataSourceDictFactory = lambda *d: DataSourceDict(*d)
) -> Type[DataObject]:
    """
    Takes a tuple of DataSource instances, and creates a CoreDataObject
    implementation that refers to all of them.

    This must be called for the given DataSources to be able to create
    CoreDataObject instances (as it injects a factory).
    """

    data_source_dict = data_source_dict_factory(*data_sources)

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
                self.__set_data(data)

        @property
        def type(self) -> str:  # noqa
            return self.__type

        @property
        def id(self) -> Optional[str]:  # noqa
            return self.__id

        @id.setter
        def id(self, new_id: str) -> None:  # noqa
            self.__id = new_id

        @property
        def attributes(self) -> Dict[str, Any]:
            return {
                key: getattr(self, key)
                for key in self.__get_field_names()
                if not self.__is_data_object(key)
            }

        @property
        def to_one_relationships(self) -> Dict[str, Optional[DataObject]]:
            if not self.__relational:
                raise NotRelationalError(self)
            return one_dict_factory(self)

        @property
        def to_many_relationships(self) -> Dict[str, Iterable[DataObject]]:
            if not self.__relational:
                raise NotRelationalError(self)
            return many_dict_factory(self)

        @property
        def _to_one_objects(self) -> Dict[str, DataObject]:
            field_names = self.__get_field_names()
            return {
                k: getattr(self, k) for k in field_names
                if self.__is_data_object(k)
            }

        @property
        def __relational(self) -> bool:
            """Whether the hosting DataSource is relational or not"""

            return isinstance(self.host, Relational)

        def __set_data(self, data: DataDict) -> None:
            """Sets the data as given to the constructor."""
            for key, value in data.items():
                setattr(self, key, value)

        def __is_data_object(self, name: str) -> bool:
            value = getattr(self, name)
            return isinstance(value, DataObject)

        def __get_field_names(self) -> List[str]:
            return [
                v for v in vars(self)
                if not v.startswith('_')
                and v not in self.__NON_FIELD_NAMES
            ]

        @property
        def host(self) -> DataSource:
            return data_source_dict[self.type]

    def core_data_object_factory(
        type_: str,
        id_: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> DataObject:

        return CoreDataObject(type_, id_=id_, data=data)

    for ds in data_sources:
        ds.data_object_factory = core_data_object_factory

    return CoreDataObject
