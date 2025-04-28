# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable

from ._writer import _Writer
from .detail_getter import DetailGetter
from .relational import Relational
from ..datasource_filter import DataSourceFilter


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
        source_object_ids: Iterable[str] | None = None,
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

    def _filter_by_source_type(
        self,
        summary_objects: Iterable[DataObject],
        source_object_type: str,
    ) -> list[DataObject]:

        return [
            s for s in summary_objects
            if s.source_object_type == source_object_type
        ]

    def _get_object_filters(
        self,
        source_object_type: str | None,
        source_object_ids: Iterable[str] | None,
    ) -> Iterable[DataSourceFilter]:

        if not self.__source_ids:
            return [self._object_filters]

        source_objs = list(
            self.get_by_ids(
                self._source_object_type,
                self.__source_ids
            )
        )

        if not source_objs:
            return [self._object_filters]

        rel_config = self.relationship_config.get(self._source_object_type)
        if not rel_config:
            return [self._object_filters]
        rel_names = rel_config.to_one if rel_config.to_one else {}

        and_extra = {}
        for rel_name in rel_names:
            and_extra |= self.__add_relationship_filter_term(
                source_objs,
                rel_name
            )

        if not self._object_filters:
            return DataSourceFilter(
                and_=and_extra
            )

        if self._object_filters.and_ is None:
            self._object_filters.and_ = and_extra
        else:
            self._object_filters.and_ |= and_extra

        return [self._object_filters]