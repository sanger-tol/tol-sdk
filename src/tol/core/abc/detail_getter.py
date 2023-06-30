# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

if typing.TYPE_CHECKING:
    from ..data_object import DataObject


class DetailGetter(ABC):
    """
    Gets an Iterable of (Optional) DataObject instances given an
    Iterable of ID strings.
    """

    @abstractmethod
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Iterable[Optional[DataObject]]:
        """
        Gets an Iterable of DataObject instances, of specified object_type,
        with their id's equal to those given in the object_ids Iterable (or
        None if the id at that position is not found).
        """
