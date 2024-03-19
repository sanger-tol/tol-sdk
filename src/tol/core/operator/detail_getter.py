# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable, Optional

if typing.TYPE_CHECKING:
    from ..data_object import DataObject

from more_itertools import chunked


class DetailGetter(ABC):
    """
    Gets an Iterable of (Optional) DataObject instances given an
    Iterable of ID strings.
    """
    page_size = 20

    def get_by_ids(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Iterable[Optional[DataObject]]:
        """
        Gets an Iterable of DataObject instances, of specified object_type,
        with their id's equal to those given in the object_ids Iterable (or
        None if the id at that position is not found).
        This splits up the request to get_by_id into sensible size
        batches, so we can safely pass a long list to this method
        """
        for chunk in chunked(object_ids, self.page_size):
            yield from self.get_by_id(object_type, chunk)

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

    def get_one(
        self,
        object_type: str,
        object_id: str
    ) -> Optional[DataObject]:
        """
        Gets the individual `DataObject` instance, of specified object_type
        and object_id, or returns `None` if not found.
        """

        return list(
            self.get_by_id(object_type, [object_id])
        )[0]
