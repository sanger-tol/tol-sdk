# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable

from .detail_getter import DetailGetter
from .relational import Relational
from ..datasource_filter import DataSourceFilter


if typing.TYPE_CHECKING:
    from ..data_object import DataObject


class Summariser(
    DetailGetter,
    Relational,
    ABC
):

    @abstractmethod
    def _summarise(
        self,
        summary_object: DataObject,
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

        source_objs = list(
            self.get_by_ids(
                source_object_type,
                source_object_ids,
            )
        )

        for s in filtered_summaries:
            first_group_by: str = s.group_by[0]
            relationship_hops = '.'.join(
                first_group_by.split('.')[:-1]
            )
            relationship_id_target = f'{relationship_hops}.id'

            relationship_ids_raw = (
                o.get_field_by_name(relationship_id_target)
                for o in source_objs
                if o is not None
            )
            relationship_ids: list[str] = [
                i for i in relationship_ids_raw
                if i is not None
            ]

            ext_and = {
                relationship_id_target: {
                    'in_list': {
                        'value': relationship_ids
                    }
                }
            }

            self._summarise(
                s,
                ext_and=ext_and,
            )

    def _mix_in_ext_and(
        self,
        object_filters: dict[str, Any] | None,
        ext_and: dict[str, Any] | None,
    ) -> DataSourceFilter:

        if not ext_and:
            return DataSourceFilter(
                and_=object_filters,
            )

        if not object_filters:
            return DataSourceFilter(
                and_=ext_and,
            )

        return DataSourceFilter(
            object_filters | ext_and,
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
