# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from itertools import islice
from typing import Iterable, Optional

from ...core.datasource_error import DataSourceError

if typing.TYPE_CHECKING:
    from ..data_object import DataObject
    from ..relationship import RelationshipConfig
    from ..session import OperableSession


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
        relationship_name: str,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Optional[DataObject]:
        """
        Gets the to-one relation DataObject, given a source DataObject and the
        name of the relationship within the config.
        """

    @abstractmethod
    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[DataObject]:
        """
        Gets the Iterable of to-many relation DataObject instances, given a source
        DataObject and the name of the relationship within the config.
        """

    def get_to_many_relations_page(
        self,
        source: DataObject,
        relationship_name: str,
        page: int,
        page_size: int,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[DataObject]:
        """
        Slices the `Relational().get_to_many_relations()` `Iterable` into pages.

        This can be overriden if a more efficient method is available.
        """

        iter_many = self.get_to_many_relations(source, relationship_name)
        start = (page - 1) * page_size
        stop = page * page_size

        return islice(iter_many, start, stop)

    def get_recursive_relation(
        self,
        source: DataObject,
        relationship_hops: list[str],
        requested_fields: list[str] | None = None
    ) -> DataObject:
        """
        Recursively get to-one relation `DataObject` instances, using the
        names defined in `relationship_hops`, returning the last one.
        """

        if not relationship_hops:
            return source

        first_hop = relationship_hops[0]
        target = self.get_to_one_relation(source, first_hop)

        if target is None:
            return None

        return self.get_recursive_relation(target, relationship_hops[1:])

    def validate_to_one_recurse(
        self,
        source_type: str,
        relationship_hops: list[str]
    ) -> None:
        """Raises a `DataSourceError` on a bad relationship name"""

        if not relationship_hops:
            return

        relationship_name = relationship_hops[0]
        self.validate_to_one_relationship(source_type, relationship_name)
        target_type = self.__get_relationship_target(
            source_type,
            relationship_name
        )
        self.validate_to_one_recurse(target_type, relationship_hops[1:])

    def validate_to_one_relationship(
        self,
        object_type: str,
        relationship_name: str
    ) -> None:
        """
        Validates that the specified `relationship_name` is defined on
        the given `object_type`.
        """

        to_one = self.relationship_config[object_type].to_one

        if relationship_name not in to_one:
            self.__raise_bad_to_one_relationsip(object_type, relationship_name)

    def __raise_bad_to_one_relationsip(
        self,
        object_type: str,
        relationship_name: str
    ) -> None:

        detail = (
            f'No to-one relationship "{relationship_name}" '
            f'exists on type {object_type}.'
        )
        raise DataSourceError(
            title='Bad Relationship Name',
            detail=detail,
            status_code=400
        )

    def __get_relationship_target(
        self,
        object_type: str,
        relationship_name: str
    ) -> str:

        to_one = self.relationship_config[object_type].to_one
        return to_one[relationship_name]
