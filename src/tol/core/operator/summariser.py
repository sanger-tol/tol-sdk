# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from functools import reduce
from typing import Any, Iterable

from ._writer import _Writer
from .detail_getter import DetailGetter
from .relational import Relational
from ..relationship import RelationshipConfig


if typing.TYPE_CHECKING:
    from ..data_object import DataObject


DataObjectUpdate = tuple[str, dict[str, Any]]


class Summariser(
    _Writer,
    DetailGetter,
    Relational,
    ABC
):

    @abstractmethod
    def _summarise(
        self,
        summary_objects: DataObject,
        ext_and: dict[str, Any] | None = None,
    ) -> None:
        """
        Summarises according to the given `list` of `DataObject`
        summary instances.
        """

    def summarise_all(
        self,
        summary_objects: Iterable[DataObject],
    ) -> None:
        """
        Summarises, across all types, using the given summary
        object-config instances.
        """

        for obj in summary_objects:
            self._summarise(obj)

    def summarise_type(
        self,
        summary_objects: Iterable[DataObject],
        source_object_type: str,
    ) -> None:
        """
        Summarises, for only the given `object_type`, using the given summary
        object-config instances.
        """

        filtered_summaries = self._filter_by_source_type(
            summary_objects,
            source_object_type,
        )

        for obj in filtered_summaries:
            self._summarise(obj)

    def resummarise_by_ids(
        self,
        summary_objects: Iterable[DataObject],
        source_object_type: str,
        source_object_ids: Iterable[str],
    ) -> None:
        """
        More restrictive than `summarise_all()`

        Re-summarises, using the given summary instances, only the set of changes
        affecting the `DataObject` instances of given `object_type` and
        `object_ids`.
        """

        filtered_summaries = self._filter_by_source_type(
            summary_objects,
            source_object_type,
        )
        ids = list(source_object_ids)

        def __none_coalesce_ones(
            config: RelationshipConfig,
        ) -> dict[str, str]:

            if not config.to_one:
                return {}
            else:
                return config.to_one

        def __get_relationship_names(
            d_type: str,
        ) -> list[str]:

            return [
                rel_name
                for k_d_type, rel_config in self.relationship_config.items()
                for rel_name in __none_coalesce_ones(rel_config)
                if k_d_type == d_type
            ]

        for s in filtered_summaries:
            rel_names = __get_relationship_names(s.destination_object_type)
            if not rel_names:
                continue

            for rel_name in rel_names:
                ext_and = {
                    f'{rel_name}.id': {
                        'in_list': {
                            'value': ids
                        }
                    }
                }

                self._summarise(
                    s,
                    source_object_type=source_object_type,
                    ext_and=ext_and,
                )

    def _filter_by_source_type(
        self,
        summary_objects: Iterable[DataObject],
        source_object_type: str,
    ) -> list[DataObject]:

        return [
            s for s in summary_objects
            if s.source_object_type == source_object_type
        ]
