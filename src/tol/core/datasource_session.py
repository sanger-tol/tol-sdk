# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import reduce
from itertools import chain
from typing import Dict, Iterable, List

from .data_object import DataObject

if typing.TYPE_CHECKING:
    from tol.core.datasource import DataSource


UpsertDict = Dict[str, List[DataObject]]


class DataSourceSession:
    def __init__(self, data_source: DataSource):
        self.__data_source: DataSource = data_source
        self.__upserts: Iterable[DataObject] = []

    def commit(self) -> None:
        self.__perform_upserts()

    def upsert(self, objects: Iterable[DataObject]) -> None:
        """
        This operation is deferred until after a commit.
        """
        self.__upserts = chain(
            self.__upserts,
            objects
        )

    def __enter__(self) -> DataSourceSession:
        return self

    def __exit__(self, type_, value_, tb_) -> None:
        self.commit()

    def __perform_upserts(self) -> None:
        separated_upserts = self.__separate_upserts()
        for object_type, objects in separated_upserts.items():
            self.__data_source.upsert(
                object_type,
                objects
            )

    def __separate_upserts(self) -> UpsertDict:
        return reduce(
            lambda upsert_dict, obj: (
                self.__accumulate_upsert(upsert_dict, obj)
            ),
            self.__upserts,
            {}
        )

    def __accumulate_upsert(
        self,
        upsert_dict: UpsertDict,
        data_object: DataObject
    ) -> UpsertDict:

        object_type = data_object.object_type
        if object_type in upsert_dict:
            upsert_dict[object_type].append(data_object)
        else:
            upsert_dict[object_type] = [data_object]
        return upsert_dict
