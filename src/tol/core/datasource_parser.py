# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar


In = TypeVar('In')
Out = TypeVar('Out')


class DataSourceParser(ABC, Generic[In, Out]):
    """
    Parses resources from the format `In` to the format `Out`
    """
    @abstractmethod
    def parse(self, transfer: In) -> Out | None:
        """
        Parses an individual transfer resource to a
        `DataObject` instance
        """
        raise NotImplementedError

    def parse_iterable(
        self, transfers: Iterable[In]
    ) -> Iterable[Out | None]:
        """
        Uses the subclass's implementation of `parse`
        to parse an iterable of transfer resources
        """
        return (self.parse(t) for t in transfers)
