# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .session import UpsertSession
from ..core.data_object import DataObject


class ObjectTypeUnspecifiedError(Exception):
    """
    Raised by a SingleTypeUpserter if an object_type is not provided.
    """
    def __init__(self) -> None:
        super().__init__(
            'This Upserter instance can only upsert objects of a '
            'single type per call. When calling upsert_session(), '
            'the keyword argument object_type must be provided.'
        )


class Upserter(ABC):
    """
    An ABC mixin to declare support for upserting DataObjects
    """

    @abstractmethod
    def upsert(
        self,
        data_objects: Iterable[DataObject],
        object_type: Optional[str] = None
    ) -> None:
        """
        Takes an iterable of DataObject instances, and upserts them.
        i.e. creates them if they don't already exist, and updates the
        existing DataObject if it does.

        object_type can optionally be specified, to indicate that all of
        the data_objects are of the same type. On some Upserter instances,
        this is required (e.g. ElasticDataSource).
        """

    def upsert_session(
        self,
        object_type: Optional[str] = None
    ) -> UpsertSession:
        """
        Creates a session for batching upsert calls on Iterables of DataObject
        instances.

        object_type can optionally be specified, to indicate that all of
        the data_objects will be of the same type. On some Upserter instances,
        this is required (e.g. ElasticDataSource).
        """
        return UpsertSession(self, object_type=object_type)


class SingleTypeUpserter(Upserter, ABC):
    """
    An Upserter for which a single object_type, that is the same for all given
    objects, must be provided to upsert_session().
    """

    def upsert_session(self, object_type: Optional[str] = None) -> UpsertSession:
        """
        Creates a session for batching upsert calls on Iterables of DataObject
        instances.

        On this instance, object_type must be specified, to indicate the (singlular) type
        of all of the data_objects.
        """
        if object_type is None:
            raise ObjectTypeUnspecifiedError()
        return super().upsert_session(object_type=object_type)
