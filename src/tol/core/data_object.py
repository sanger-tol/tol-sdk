# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional

if typing.TYPE_CHECKING:
    from .datasource import DataSource


DataDict = dict[str, Any]


class DataObject(ABC):
    """
    The ABC for the unit of data on which a DataSource instance
    operates - representing the lingua franca of DataSource instances,
    and declaring all abstract properties that are needed.
    """

    @property
    @abstractmethod
    def type(self) -> str:  # noqa
        """
        The type of this object (e.g. species/specimens/samples).
        """

    @property
    @abstractmethod
    def id(self) -> Optional[str]:  # noqa
        """
        A unique ID by which to identify this object within
        its type.
        """

    @property
    @abstractmethod
    def attributes(self) -> dict[str, Any]:
        """
        A dictionary of key:attribute pairs, where an attribute
        is any entry on the object that is none of an ID, type,
        or relationship.
        """

    @property
    @abstractmethod
    def to_one_relationships(self) -> dict[str, Optional[DataObject]]:
        """
        A dictionary of relationships, where this object refers to
        precisely one other.
        """

    @property
    @abstractmethod
    def to_many_relationships(self) -> dict[str, Iterable[DataObject]]:
        """
        A dictionary of relationships, where many objects refer to
        precisely this object.
        """

    @property
    @abstractmethod
    def host(self) -> DataSource:
        """
        The DataSource instance that manages DataObject instances of this type
        """

    @property
    @abstractmethod
    def _to_one_objects(self) -> dict[str, DataObject]:
        """
        The name: attribute mapping for `DataObject`s set on this instance.

        N.B. - This is not equivalent to `to_one_relationships`, as that merges
        both set `DataObject` instances and fetched relations from the
        `DataSource`.
        """
