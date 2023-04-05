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
    def __init__(
        self,
        data_source: DataSource,
        multi_type: bool = False
    ):
        self.__data_source: DataSource = data_source
        self.__upserts: Iterable[DataObject] = []
        self.__multi_type = multi_type

    def commit(self) -> None:
        self.__perform_upsert()

    def upsert(self, objects: Iterable[DataObject]) -> None:
        """
        This upsert operation differs from DataSource().upsert()
        in a few ways:

        - It is deferred until after a commit() call.
        - Objects of mixed object_type can be given
        """
        self.__upserts = chain(
            self.__upserts,
            objects
        )

    def __enter__(self) -> DataSourceSession:
        return self

    def __exit__(self, type_, value_, tb_) -> None:
        self.commit()

    def __perform_upsert(self) -> None:
        if self.__multi_type is True:
            self.__perform_multi_type_upsert()
        else:
            self.__perform_single_type_upserts()

    def __perform_single_type_upserts(self) -> None:
        separated_upserts = self.__separate_upserts()
        for object_type, objects in separated_upserts.items():
            self.__data_source.upsert(
                object_type,
                objects
            )

    def __perform_multi_type_upsert(self) -> None:
        self.__data_source.multi_type_upsert(
            self.__upserts
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
        objects = upsert_dict.get(object_type, [])
        objects.append(data_object)
        upsert_dict[object_type] = objects
        return upsert_dict
