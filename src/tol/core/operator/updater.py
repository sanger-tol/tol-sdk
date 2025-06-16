# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional

from ._writer import _Writer

if typing.TYPE_CHECKING:
    from ..data_object import DataObject, ErrorObject
    from ..session import OperableSession


DataObjectUpdate = tuple[str, dict[str, Any]]


class Updater(_Writer, ABC):
    """
    Updates existing DataObject instances.
    """

    @abstractmethod
    def update(
        self,
        object_type: str,
        updates: Iterable[DataObjectUpdate],
        session: Optional[OperableSession] = None,
        **kwargs: Any,
    ) -> Iterable[DataObject | ErrorObject] | None:
        """
        Takes a type and an `Iterable` of ID-`DataObjectUpdate` pairs.

        For each pair, the existing `DataObject` identified by the ID is
        updated using the `DataObjectUpdate` dict of new values. Values
        that aren't mentioned remain the same as previously.
        """
