# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from itertools import chain
from typing import Dict, Iterable, List

from .data_object import DataObject
from .data_object_dict import DataObjectDict

if typing.TYPE_CHECKING:
    from .datasource import DataSource


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
            self.__perform_upsert_multiple_type()
        else:
            self.__perform_single_type_upserts()

    def __perform_single_type_upserts(self) -> None:
        separated_upserts = self.__separate_upserts()
        for object_type, objects in separated_upserts.items():
            self.__data_source.upsert(
                object_type,
                objects
            )

    def __perform_upsert_multiple_type(self) -> None:
        self.__data_source.upsert_multiple_type(
            self.__upserts
        )

    def __separate_upserts(self) -> Dict[str, List[DataObject]]:
        upsert_dict = DataObjectDict()
        upsert_dict.add_bulk(self.__upserts)
        return upsert_dict
