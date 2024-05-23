# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

if typing.TYPE_CHECKING:
    from ..data_object import DataObject
    from ..session import OperableSession


class Inserter(ABC):
    """
    Inserts new `DataObject` instances into a `DataSource`.

    Fails if they are already present.
    """

    @abstractmethod
    def insert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:
        """
        Inserts the given `DataObject` instances
        of specified type.
        """
