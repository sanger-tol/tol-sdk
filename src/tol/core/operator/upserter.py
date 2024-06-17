# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ._writer import _Writer

if typing.TYPE_CHECKING:
    from ..data_object import DataObject
    from ..session import OperableSession


class Upserter(_Writer, ABC):
    """
    Upserts DataObject instances.
    """

    @abstractmethod
    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None
    ) -> None:
        """
        Takes a type and an `Iterable` of `DataObject` instances, on
        each of which to perform an "upsert", i.e.:

        - insert    - if the `DataObject` is new to the `DataSource`
        - update    - if the `DataObject` is not new
        """
