# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import itertools
import typing
from abc import ABC
from typing import Any, Iterable, Optional

import more_itertools

from ._writer import _Writer

if typing.TYPE_CHECKING:
    from ..data_object import DataObject, ErrorObject
    from ..session import OperableSession


class Upserter(_Writer, ABC):
    """
    Upserts DataObject instances.
    """
    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None,
        **kwargs: Any
    ) -> Iterable[DataObject | ErrorObject] | None:
        """
        Takes a type and an `Iterable` of `DataObject` instances, on
        each of which to perform an "upsert", i.e.:

        - insert    - if the `DataObject` is new to the `DataSource`
        - update    - if the `DataObject` is not new

        We previde a default implementation that calls `upsert_batch`
        """
        upserted = ()
        for batch in more_itertools.chunked(objects, self.write_batch_size):
            upserted = itertools.chain(upserted, self.upsert_batch(
                object_type,
                batch,
                session=session,
                **kwargs
            ))
        return upserted

    def upsert_arbitary_type(
        self,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None,
        **kwargs: Any,
    ) -> Iterable[DataObject | ErrorObject]:
        """
        Calls `upsert()` internally, using contiguous slices of
        `DataObject` instances with the same `type`.

        Unlike with other `upsert*` methods, you always need to
        exhuast the iterable returned by this method (e.g. by a `for`
        loop or using `list()`).
        """

        split_iter = more_itertools.split_when(
            objects,
            lambda x, y: x.type != y.type,
        )

        upserted_iter = (
            self.upsert(
                split[0].type,
                split,
                session=session,
            )
            for split in split_iter
        )

        return itertools.chain.from_iterable(
            upserted
            for upserted in upserted_iter
            if upserted is not None
        )

    def upsert_batch(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None,
        **kwargs: Any,
    ) -> Iterable[DataObject | ErrorObject] | None:
        raise NotImplementedError()
