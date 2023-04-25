# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Iterable, Tuple

from ...core import (
    CoreDataObject,
    DataId,
    DataSource,
    DataSourceConfig,
    DataSourceFilter,
    DataSourceSession,
    unsupported
)


class SqlDataSource(DataSource):
    """
    The DataSource for Sqlalchemy
    """

    def __init__(self, config: DataSourceConfig):
        expected = ['db']
        super().__init__(config, expected)

    def session(self) -> DataSourceSession:
        """
        Returns a DataSourceSession object for batching upserts.

        This always operates simultaneously on multiple types of DataObject
        """
        return DataSourceSession(self, multi_type=True)

    @unsupported
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ) -> Iterable[CoreDataObject]:
        pass

    @unsupported
    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Tuple[Iterable[CoreDataObject], int]:
        pass

    @unsupported
    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[CoreDataObject]:
        pass

    @unsupported
    def upsert(
        self,
        object_type: str,
        objects: Iterable[CoreDataObject],
        **kwargs
    ) -> None:
        pass

    def upsert_multiple_type(
        self,
        objects: Iterable[CoreDataObject],
        **kwargs
    ) -> None:
        """
        Takes an iterable of DataObjects of any (and mixed) object_type,
        and for each, performs either:

        - an insert (if they don't exist already)
        - an update (if they do)

        This endpoint will work out the order in which they must be upserted
        automatically.
        """
