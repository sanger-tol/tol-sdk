# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class Deleter(ABC):
    """
    Deletes DataObject instances.
    """

    @abstractmethod
    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> None:
        """
        Takes a type, and the IDs of the `DataObject` to delete
        of the stated type.
        """
