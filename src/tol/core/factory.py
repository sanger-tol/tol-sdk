# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
import typing
from abc import ABC
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Protocol,
    Type,
    Union
)

from .data_object import DataDict, DataObject
from .data_source_dict import DataSourceDict
from .datasource_error import DataSourceError, NotRelationalError
from .operator import Relational
from .relationship import RelationshipConfig, ToManyDict, ToOneDict

if typing.TYPE_CHECKING:
    from .datasource import DataSource


ToOne = dict[str, Optional[DataObject]]
ToMany = dict[str, Iterable[DataObject]]


class DataObjectFactory(Protocol):
    """
    A factory that takes several args and kwargs, and returns
    a new DataObject instance.
    """

    def __call__(
        self,
        type_: str,

        id_: Optional[str] = None,
        attributes: Dict[str, Any] | None = None,
        to_one: ToOne | None = None,
        to_many: ToMany | None = None
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


def _local_name(__name: str) -> bool:
    __PROPERTY_NAMES = [  # noqa N806
        'id',
        'type',
        'attributes',
        'to_one_relationships',
        'to_many_relationships',
        'get_field_by_name'
    ]

    return (
        __name.startswith('_')
        or __name in __PROPERTY_NAMES
    )


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

        def __init__(
            self,
            type_: str,
            id_: Optional[str] = None,
            attributes: DataDict | None = None,
            to_one: ToOne | None = None,
            to_many: ToMany | None = None,
            stub: bool = False,
            stub_types: Optional[Iterable[str]] = None
        ):
            self.__id = id_
            self.__type = type_
            self.__attributes = attributes if attributes is not None else {}
            self.__to_one_objects = to_one if to_one is not None else {}
            if stub and id_ is None:
                raise DataSourceError('ID must be set if stub is True')
            self.__stub_value = stub
            self.__stub_types = stub_types
            if self.__relational:
                self.__to_one_relations = one_dict_factory(self)
                self.__to_many_relations = many_dict_factory(self)

            if to_many:
                logging.warning(
                    'Setting of to_many relations is unsupported'
                )

        def __str__(self) -> str:
            dump = f'type="{self.type}"'

            if self.id is not None:
                dump += f', id="{self.id}"'

            return f'CoreDataObject({dump})'

        def __getattribute__(self, __name: str) -> Any:
            if _local_name(__name):
                return object.__getattribute__(self, __name)

            if self.__stub_value:
                self.__unstub()

            if __name in self.__to_one_names:
                if __name in self._to_one_objects:
                    return self._to_one_objects[__name]
                return self.to_one_relationships.get(__name)

            if __name in self.__to_many_names:
                return self.to_many_relationships.get(__name, [])

            return self.__attributes.get(__name)

        def __setattr__(self, __name: str, __value: Any) -> None:
            if _local_name(__name):
                object.__setattr__(self, __name, __value)
            elif __name in self.__to_one_names:
                self._to_one_objects[__name] = __value
            elif __name in self.__to_many_names:
                raise DataSourceError(
                    title='Read-only To-Many',
                    detail='To-many relations are readonly',
                    status_code=400
                )
            else:
                self.__attributes[__name] = __value

        def __unstub(self) -> None:
            self.__stub_value = False
            # Actually get this object from the datasource
            possible_types = self.__stub_types if self.__stub_types is not None else [self.__type]
            for t in possible_types:
                object_from_datasource = data_source_dict[t].get_one(t, self.__id)
                if object_from_datasource is not None:
                    self.__type = object_from_datasource.type
                    self.__attributes = object_from_datasource.attributes
                    self.__to_one_objects = object_from_datasource.to_one_objects
                    break

        @property
        def type(self) -> str:  # noqa
            if self.__stub_value and self.__type is None:
                self.__unstub()
            return self.__type

        @property
        def id(self) -> Optional[str]:  # noqa
            return self.__id

        @id.setter
        def id(self, new_id: str) -> None:  # noqa
            self.__id = new_id

        @property
        def attributes(self) -> Dict[str, Any]:
            if self.__stub_value:
                self.__unstub()
            return self.__attributes

        @property
        def to_one_relationships(self) -> Dict[str, Optional[DataObject]]:
            if not self.__relational:
                raise NotRelationalError(self)
            return self.__to_one_relations

        @property
        def to_many_relationships(self) -> Dict[str, Iterable[DataObject]]:
            if not self.__relational:
                raise NotRelationalError(self)
            return self.__to_many_relations

        @property
        def _to_one_objects(self) -> Dict[str, DataObject]:
            return self.__to_one_objects

        @property
        def __relational(self) -> bool:
            """Whether the hosting DataSource is relational or not"""

            return isinstance(self._host, Relational)

        @property
        def __relationship_config(self) -> Optional[RelationshipConfig]:
            return self._host.relationship_config.get(self.type)

        @property
        def __to_one_names(self) -> list[str]:
            if not self.__relational:
                return []
            cfg = self.__relationship_config
            return (
                [] if cfg is None or cfg.to_one is None
                else list(cfg.to_one.keys())
            )

        @property
        def __to_many_names(self) -> list[str]:
            if not self.__relational:
                return []
            cfg = self.__relationship_config
            return (
                [] if cfg is None or cfg.to_many is None
                else list(cfg.to_many.keys())
            )

        @property
        def _host(self) -> Union[DataSource, Relational]:
            return data_source_dict[self.type]

    def core_data_object_factory(
        type_: str,
        id_: Optional[str] = None,
        attributes: Dict[str, Any] | None = None,
        to_one: ToOne | None = None,
        to_many: ToMany | None = None,
        stub: bool = False,  # Set stub if only type and id are given on creation
        stub_types: Optional[Iterable[str]] = None
    ) -> DataObject:

        return CoreDataObject(
            type_,
            id_=id_,
            attributes=attributes,
            to_one=to_one,
            to_many=to_many,
            stub=stub,
            stub_types=stub_types
        )

    for ds in data_sources:
        ds.data_object_factory = core_data_object_factory

    return CoreDataObject
