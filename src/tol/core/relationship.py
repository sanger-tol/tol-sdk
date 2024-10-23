# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional

from cachetools import LFUCache

from .operator import Relational

if typing.TYPE_CHECKING:
    from .data_object import DataObject


RelationshipDump = Dict[str, Dict[str, str]]


@dataclass
class RelationshipConfig:
    """
    Describes the configuration of relationships on a specific
    type of DataObject.

    The keys of each Optional[Dict] are the names of a relationship,
    and the values are the type of DataObject instances to which they
    are directed. For foreign keys, the values are the name of the
    attribute in this class (to_one) or the foreign class (to_many)
    that implements the relationship.
    """

    to_one: Optional[Dict[str, str]] = None
    to_many: Optional[Dict[str, str | List[str]]] = None
    foreign_keys: Optional[Dict[str, str]] = None

    def to_dict(self) -> Optional[RelationshipDump]:
        if self.empty:
            return None
        return self.__build_dict()

    @property
    def empty(self) -> bool:
        return self.to_one is None and self.to_many is None

    def __build_dict(self) -> RelationshipDump:
        __dict = {}
        if self.to_one is not None:
            __dict['one'] = self.to_one
        if self.to_many is not None:
            __dict['many'] = self.to_many
        if self.foreign_keys is not None:
            __dict['foreign_keys'] = self.foreign_keys
        return __dict

    def __str__(self) -> str:
        return str(self.to_dict())


class ToManyDict(Mapping):
    """A Dict that loads items lazily and memoizes the result"""

    def __init__(self, source: DataObject) -> None:
        self.__dict = LFUCache(100000)
        self.__source = source
        self.__host: Relational = source._host
        self.__keys = self.__get_keys()

    def __getitem__(self, __k: str) -> Iterable[DataObject]:
        if __k not in self.__keys:
            raise KeyError()
        if __k not in self.__dict:
            return self.__get_many_objects(__k)
        else:
            return self.__dict[__k]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__keys)

    def __len__(self) -> int:
        return len(self.__keys)

    def __get_many_objects(self, __k: str) -> Iterable[DataObject]:
        many_objects = self.__host.get_to_many_relations(
            self.__source,
            __k
        )
        self.__dict[__k] = many_objects
        return many_objects

    def __get_keys(self) -> List[str]:
        config = self.__config
        if config is None or config.to_many is None:
            return []
        return list(config.to_many.keys())

    @property
    def __config(self) -> Optional[RelationshipConfig]:
        type_ = self.__source.type
        return self.__host.relationship_config.get(type_)


class ToOneDict(Mapping):
    """
    A dict that implements to-one relationships, and supports:

    - lazy loading
    - memoisation
    - overwriting

    This is only to be used by a CoreDataObject.
    """

    def __init__(self, source: DataObject) -> None:
        self.__dict = LFUCache(100000)
        self.__source = source
        self.__host: Relational = source._host
        self.__keys = self.__get_keys()

    def __getitem__(self, __k: str) -> Optional[DataObject]:
        if __k not in self.__keys:
            raise KeyError()
        set_to_one_objects = self.__source._to_one_objects
        if __k in set_to_one_objects:
            return set_to_one_objects[__k]
        return self.__get_or_cached(__k)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__keys)

    def __len__(self) -> int:
        return len(self.__keys)

    def __get_keys(self) -> List[str]:
        config = self.__config
        if config is None or config.to_one is None:
            return []
        return list(config.to_one.keys())

    def __get_one_object(self, __k: str) -> Optional[DataObject]:
        one_object = self.__host.get_to_one_relation(self.__source, __k)
        self.__dict[__k] = one_object
        return one_object

    def __get_or_cached(self, __k: str) -> Optional[DataObject]:
        if __k not in self.__dict:
            return self.__get_one_object(__k)
        else:
            return self.__dict[__k]

    @property
    def __config(self) -> Optional[RelationshipConfig]:
        type_ = self.__source.type
        return self.__host.relationship_config.get(type_)
