# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractproperty
from typing import Any, Dict, Iterable, Optional


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
    def to_one_relationships(self) -> Dict[str, Optional[DataObject]]:
        """
        A dictionary of relationships, where this object refers to
        precisely one other.
        """

    @abstractproperty
    def to_many_relationships(self) -> Dict[str, Iterable[DataObject]]:
        """
        A dictionary of relationships, where many objects refer to
        precisely this object.
        """
