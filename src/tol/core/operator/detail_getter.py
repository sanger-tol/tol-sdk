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

from more_itertools import chunked, seekable


class DetailGetter(ABC):
    """
    Gets an Iterable of (Optional) DataObject instances given an
    Iterable of ID strings.
    """
    page_size = 20

    def get_by_ids(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[Optional[DataObject]]:
        """
        Gets an Iterable of DataObject instances, of specified object_type,
        with their id's equal to those given in the object_ids Iterable (or
        None if the id at that position is not found).
        This splits up the request to get_by_id into sensible size
        batches, so we can safely pass a long list to this method
        """

        for chunk in chunked(object_ids, self.page_size):
            yield from self.get_by_id(
                object_type,
                chunk,
                requested_fields=requested_fields,
            )

    @abstractmethod
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[Optional[DataObject]]:
        """
        Gets an Iterable of DataObject instances, of specified object_type,
        with their id's equal to those given in the object_ids Iterable (or
        None if the id at that position is not found).
        """

    def get_one(
        self,
        object_type: str,
        object_id: str,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Optional[DataObject]:
        """
        Gets the individual `DataObject` instance, of specified object_type
        and object_id, or returns `None` if not found.
        """

        return list(
            self.get_by_id(
                object_type,
                [object_id],
                requested_fields=requested_fields
            )
        )[0]

    # A helper method to ensure that the order of the returned objects
    # matches the order of the input ids
    def sort_by_id(
        self,
        data_objects: Iterable[DataObject],
        object_ids: Iterable[int | str]
    ) -> Iterable[DataObject | None]:

        seekable_objects = seekable(data_objects)
        for id_ in object_ids:
            seekable_objects.seek(0)
            for obj in seekable_objects:
                if obj.id == id_:
                    yield obj
                    break
            else:
                yield None
