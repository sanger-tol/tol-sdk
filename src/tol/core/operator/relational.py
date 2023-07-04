# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

if typing.TYPE_CHECKING:
    from ..data_object import DataObject
    from ..relationship import RelationshipConfig


class Relational(ABC):
    """
    Augments a DataSource to support relationships between hosted
    DataObject types.
    """

    @property
    @abstractmethod
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        """
        The configuration of relationships (both to-one and to-many) between
        the types of DataObject instances managed by this DataSource instance.
        """

    @abstractmethod
    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:
        """
        Gets the to-one relation DataObject, given a source DataObject and the
        name of the relationship within the config.
        """

    @abstractmethod
    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Iterable[DataObject]:
        """
        Gets the Iterable of to-many relation DataObject instances, given a source
        DataObject and the name of the relationship within the config.
        """
