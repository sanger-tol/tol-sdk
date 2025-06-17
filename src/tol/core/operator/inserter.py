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


class Inserter(_Writer, ABC):
    """
    Inserts new `DataObject` instances into a `DataSource`.

    Fails if they are already present.
    """

    def insert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None,
        **kwargs: Any,
    ) -> Iterable[DataObject | ErrorObject] | None:
        """
        Inserts the given `DataObject` instances
        of specified type.
        """
        inserted = ()
        for batch in more_itertools.chunked(objects, self.write_batch_size):
            inserted = itertools.chain(inserted, self.insert_batch(
                object_type,
                batch,
                session=session,
                **kwargs
            ))
        return inserted

    def insert_batch(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None,
        **kwargs: Any,
    ) -> Iterable[DataObject | ErrorObject] | None:
        raise NotImplementedError()
