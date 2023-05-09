# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from itertools import chain
from typing import Iterable, Optional

from ..core.data_object import DataObject

if typing.TYPE_CHECKING:
    from .upserter import Upserter


class UpsertSessionExhaustedException(Exception):
    """
    Indicates that commit() has already been called on an
    UpsertSession instance.
    """

    def __init__(self) -> None:
        super().__init__(
            'A commit has already taken place. If you are using '
            'a "with" block, you must not explicitly call '
            'the commit() method.'
        )


class UpsertSession:
    """
    A context-manager session for batching upsert calls on
    an Upserter instance.

    Supports both:
    - multi type    - upserts objects of many supported types
                      simultaneously (default).
    - single type   - upserts objects of only one type. Specify
                      this type in the constructor.
    """

    def __init__(
        self,
        upserter: Upserter,
        object_type: Optional[str] = None
    ):
        self.__upserter = upserter
        self.__object_type = object_type
        self.__data_objects: Iterable[DataObject] = []
        self.__exhausted: bool = False

    def commit(self) -> None:
        if self.__exhausted is True:
            raise UpsertSessionExhaustedException()
        self.__perform_upserts()
        self.__exhausted = True

    def upsert(self, objects: Iterable[DataObject]) -> None:
        """
        This upsert operation differs from Upserter().upsert()
        in a few ways:

        - It is deferred until after a commit() call.
        - Objects of mixed object_type can be given, if and only if
          a single object_type was not specified in the constructor
        """
        self.__data_objects = chain(
            self.__data_objects,
            objects
        )

    def __enter__(self) -> UpsertSession:
        return self

    def __exit__(self, type_, value_, tb_) -> None:
        self.commit()

    def __perform_upserts(self) -> None:
        self.__upserter.upsert(
            self.__data_objects,
            object_type=self.__object_type
        )
