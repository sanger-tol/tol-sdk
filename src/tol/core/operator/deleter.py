# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ._writer import _Writer

if typing.TYPE_CHECKING:
    from ..data_object import ErrorObject
    from ..session import OperableSession


class Deleter(_Writer, ABC):
    """
    Deletes DataObject instances.
    """

    @abstractmethod
    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session: Optional[OperableSession] = None
    ) -> Iterable[ErrorObject | None] | None:
        """
        Takes a type, and the IDs of the `DataObject` to delete
        of the stated type.
        """
