# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ._filterable import _Filterable
from ..datasource_error import DataSourceError
from ..datasource_filter import DataSourceFilter

if typing.TYPE_CHECKING:
    from ..data_object import DataObject
    from ..session import OperableSession


class Cursor(_Filterable, ABC):
    """
    Implements cursor pagination.
    """

    @property
    def candidate_keys(self) -> dict[str, list[str]]:
        """
        The names of the fields that form the
        candidate_key for cursor pagination on
        an `object_type`.
        """

        return {
            k: ['id']
            for k in self.supported_types
        }

    @property
    @abstractmethod
    def supported_types(self) -> list[str]:
        pass

    @abstractmethod
    def get_cursor_page(
        self,
        object_type: str,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        search_after: list[str] | None = None,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> tuple[Iterable[DataObject], list[str] | None]:
        """
        Gets an `Iterable` of `DataObject` instances of the given
        `object_type`, of length given by `page_size`, from either:

        - the start (`if search_after is None`)
        - `search_after` (`if search_after is not None` i.e. an ID)

        Also returns the next `search_after` term.
        """

    def update_cursor_filters(
        self,
        search_after: list[str] | None,
        object_filters: DataSourceFilter | None
    ) -> DataSourceFilter | None:

        if search_after is None:
            return object_filters

        if len(search_after) != 1:
            raise DataSourceError(
                'Bad Cursor',
                'The `search_after` argument must specify an ID only.',
                400
            )

        if object_filters is None:
            return DataSourceFilter(
                and_={
                    'id': {
                        'gt': {
                            'value': search_after[0]
                        }
                    }
                }
            )

        if object_filters.and_ is None:
            object_filters.and_ = {}

        object_filters.and_['id'] = {
            'gt': {
                'value': search_after[0]
            }
        }
        return object_filters

    def can_use_cursor(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
    ) -> bool:

        if object_filters is None or object_filters.and_ is None:
            return True

        keys = self.candidate_keys[object_type]

        return not any(
            True for k in keys
            if k in object_filters.and_
        )

    def _get_list_by_cursor(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[DataObject]:
        """
        A usable implementation for `ListGetter.get_list()`
        using `Cursor.get_cursor_page()` internally.
        """

        search_after = None
        page_size = self.get_page_size()

        while True:
            fetched, search_after = self.get_cursor_page(
                object_type,
                page_size=page_size,
                object_filters=object_filters,
                search_after=search_after,
                session=session,
                requested_fields=requested_fields,
            )
            objs = list(fetched)

            yield from objs

            if len(objs) < page_size:
                return
