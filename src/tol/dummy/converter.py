# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, List, Optional

from .parser import Parser
from ..core import DataObject


DummyObject = dict[str, Any]
DummyTransfer = List[DummyObject]


class DummyConverter():

    """
    Converts from Dummy transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:

        self.__parser = parser

    def convert(self, input_: DummyTransfer) -> DataObject:
        """
        Converts a DummyTransfer containing a detail (single) result
        """
        return self.__parser.parse(input_)

    def convert_list(
        self,
        input_: DummyTransfer
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts a DummyTransfer containing a list of results. Also
        returns a count of the total results meeting.
        """

        return [
            self.__parser.parse(json_obj)
            for json_obj in input_
            if json_obj is not None
        ], None
