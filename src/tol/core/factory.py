# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Iterable as IterableABC
from typing import Any, Dict, Iterable, List, Optional, Protocol, Type

from .data_object import DataDict, DataObject
from .data_source_dict import DataSourceDict

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


def core_data_object(*data_sources: DataSource) -> Type[DataObject]:
    """
    Takes a tuple of DataSource instances, and creates a DataObject
    implementation that refers to all of them.

    This must be called for the given DataSources to be able to create
    DataObject instances (as it injects a factory).
    """

    class CoreDataObject(DataObject):
        """
        A DataObject that can be created outside of a DataSource, which
        should prove sufficient for most use-cases. Simply set values
        on an instance, and they will be interpreted as either:

        - to-one relationships  - if the value is a single DataObject
        - to-many relationships - if the value is any non-string Iterable
        - attributes            - otherwise

        Note there are other supported DataObject classes - any class
        that inherits from DataObject meets the criteria.
        """

        __data_source_dict: Dict[str, DataSource] = DataSourceDict(
            *data_sources
        )
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
                if self.__is_attribute(key)
            }

        @property
        def to_one_relationships(self) -> Dict[str, DataObject]:
            # add self.__data_source_dict here
            return {
                key: getattr(self, key)
                for key in self.__get_field_names()
                if self.__is_to_one_relationship(key)
            }

        @property
        def to_many_relationships(self) -> Dict[str, Iterable[DataObject]]:
            # add self.__data_source_dict here
            return {
                key: getattr(self, key)
                for key in self.__get_field_names()
                if self.__is_to_many_relationship(key)
            }

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

    def core_data_object_factory(
        type_: str,
        id_: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> DataObject:

        return CoreDataObject(type_, id_=id_, data=data)

    for ds in data_sources:
        ds.data_object_factory = core_data_object_factory

    return CoreDataObject
