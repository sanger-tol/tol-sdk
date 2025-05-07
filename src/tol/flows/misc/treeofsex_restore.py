# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from cachetools import Cache, LFUCache

if typing.TYPE_CHECKING:
    from ...elastic import ElasticDataSource
    from ...sql import SqlDataSource


IdsCache = Cache[str, list[str]]


class TreeOfSexRestorer:

    def __init__(
        self,
        sql_ds: SqlDataSource,
        elastic_ds: ElasticDataSource,
        *,
        lfu_cache_size: int = 1000,
        cache_override: IdsCache | None = None,
    ) -> None:

        self.__sql_ds = sql_ds
        self.__elastic_ds = elastic_ds

        self.__cache = self.__get_cache(
            lfu_cache_size,
            cache_override,
        )

    def restore(self) -> None:
        pass

    def __get_cache(
        self,
        lfu_cache_size: int,
        cache_override: IdsCache | None,
    ) -> IdsCache:

        if cache_override is not None:
            return cache_override

        return LFUCache(lfu_cache_size)

    def __get_child_ids(
        self,
        parent_id: str,
    ) -> list[str]:
        """
        Gets the ids of all children under
        the parent, within the tree.
        """

        # TODO is this a TREEE?????

        cached_ids = self.__cache.get(parent_id)
        if cached_ids is not None:
            return cached_ids

        # TODO more here
        fetched_ids: list[str] = []
        self.__cache[parent_id] = fetched_ids
        return fetched_ids
