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
        Summarises according to the given `DataObject`
        summary instance.
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

        Returns None, but performs summarization operations.
        """
        objects_to_summarise, _ = self.get_objects_to_summarise(
            summary_objects,
            source_object_type,
            source_object_ids,
        )

        for summary_obj, ext_and in objects_to_summarise:
            self._summarise(
                summary_obj,
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

    def get_objects_to_summarise(
        self,
        summary_objects: Iterable[DataObject],
        source_object_type: str,
        source_object_ids: Iterable[str],
    ) -> tuple[list[tuple[DataObject, dict[str, Any]]], dict[str, list[str]]]:
        """
        Helper function for resummariser_by_ids that returns the objects to be summarised
        along with their extended filter conditions.

        Returns:
            A tuple containing:
            - A list of tuples containing (summary_object, ext_and) pairs that can be used
            for summarisation.
            - A list of relationship IDs that were extracted during the process, which can
            be used for subsequent operations like enrichment.
        """
        filtered_summaries = self._filter_by_source_type(
            summary_objects,
            source_object_type,
        )

        if not filtered_summaries:
            return [], {}

        source_objs = list(
            self.get_by_ids(
                source_object_type,
                source_object_ids,
            )
        )

        result = []
        relationship_ids_by_type = {}

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

            dest_type = s.destination_object_type
            if dest_type not in relationship_ids_by_type:
                relationship_ids_by_type[dest_type] = []
            relationship_ids_by_type[dest_type].extend(relationship_ids)

            ext_and = {
                relationship_id_target: {
                    'in_list': {
                        'value': relationship_ids
                    }
                }
            }

            result.append((s, ext_and))

        for obj_type in relationship_ids_by_type:
            relationship_ids_by_type[obj_type] = list(set(relationship_ids_by_type[obj_type]))

        return result, relationship_ids_by_type
