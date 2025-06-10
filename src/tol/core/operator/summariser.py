# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable

from .detail_getter import DetailGetter
from .relational import Relational
from ..datasource_filter import AndFilter, DataSourceFilter


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

        list_ids = list(source_object_ids)

        filtered_summaries = self._filter_by_source_type(
            summary_objects,
            source_object_type,
        )

        for summary_obj in filtered_summaries:
            ext_and = self.get_and_filter_to_summarise(
                summary_obj,
                source_object_type,
                list_ids,
            )
            if not ext_and:
                continue
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
            and_=object_filters | ext_and,
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

    def get_and_filter_to_summarise(
        self,
        summary_object: DataObject,
        source_object_type: str,
        source_object_ids: Iterable[str],
    ) -> AndFilter:

        if not self.relationship_config:
            return {}

        if source_object_type not in self.relationship_config:
            return {}

        to_ones = self.relationship_config[source_object_type].to_one
        if not to_ones:
            return {}

        source_objs = list(
            self.get_by_ids(
                source_object_type,
                source_object_ids,
                requested_fields=summary_object.group_by,
            )
        )

        to_one_names = self._get_resummarised_to_one_names(
            summary_object,
            to_ones,
        )

        pairs = (
            self._ext_and_for_relationship(
                source_objs,
                relationship,
            )
            for relationship in to_one_names
        )

        return {
            k: {
                'in_list': {
                    'value': v
                }
            }
            for k, v in pairs
            if v
        }

    def _ext_and_for_relationship(
        self,
        source_objs: list[DataObject | None],
        relationship: str,
    ) -> tuple[str, list[str]]:

        relationship_id_target = f'{relationship}.id'

        relationship_ids_raw = {
            o.get_field_by_name(relationship_id_target)
            for o in source_objs
            if o is not None
        }
        relationship_ids: list[str] = [
            i for i in relationship_ids_raw
            if i is not None
        ]

        return relationship_id_target, relationship_ids

    def _get_resummarised_to_one_names(
        self,
        summary_obj: DataObject,
        to_ones: dict[str, str],
    ) -> list[str]:

        group_by: list[str] | None = summary_obj.group_by
        if not group_by:
            return list(to_ones)

        return [
            r for r in to_ones
            if any(
                g for g in group_by
                if g.startswith(r)
            )
        ]
