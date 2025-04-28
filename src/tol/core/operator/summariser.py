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
        summary_objects: list[DataObject],
        source_object_type: str | None = None,
        ext_and: dict[str, Any] = None,
    ) -> None:
        """
        Summarises according to the given `list` of `DataObject`
        summary instances.
        """

    def summarse_all(
        self,
        summary_objects: Iterable[DataObject],
    ) -> None:
        """
        Summarises, across all types, using the given summary
        object-config instances.
        """

        self._summarise(list(summary_objects))

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

        self._summarise(
            filtered_summaries,
            source_object_type=source_object_type,
        )

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

        def __reduce_func(
            d: dict[str, list[DataObject]],
            s: DataObject,
        ) -> dict[str, list[DataObject]]:

            s_existing: list[DataObject] = d.get(s.source_object_type, [])
            d[s.source_object_type] = [*s_existing, s]

            return d

        d_summaries: dict[str, list[DataObject]] = reduce(
            __reduce_func,
            filtered_summaries,
            {},
        )

        def __none_coalesce_to_many(
            config: RelationshipConfig,
        ) -> dict[str, str]:

            if not config.to_many:
                return {}
            else:
                return config.to_many

        def __get_relationship_names(
            d_type: str,
        ) -> list[str]:

            return [
                rel_name
                for k_d_type, rel_config in self.relationship_config.items()
                for rel_name in __none_coalesce_to_many(rel_config)
                if k_d_type == d_type
            ]

        for d_type, s_objs in d_summaries.items():
            rel_names = __get_relationship_names(d_type)
            import logging; logging.error(d_type); logging.error(rel_names)
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
                    s_objs,
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
