# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from . import DataObject


TransferResourceType = TypeVar('TransferResourceType')


class DataSourceParser(ABC, Generic[TransferResourceType]):
    """
    Parses transfers to and from a remote source (of type `TransferType`)
    into `DataObject` instances.
    """
    @abstractmethod
    def parse(self, transfer: TransferResourceType) -> DataObject:
        """
        Parses an individual transfer resource to a
        `DataObject` instance
        """
        raise NotImplementedError
    
    def parse_iterable(self, transfers: Iterable[TransferResourceType]) -> Iterable[DataObject]:
        """
        Uses the subclass's implementation of `parse`
        to parse an iterable of transfer resources
        """
        return (self.parse(t) for t in transfers)
