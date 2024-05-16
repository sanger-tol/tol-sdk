# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, List, Optional

from .parser import Parser
from ..core import DataObject


BoldApiObject = dict[str, Any]
BoldApiTransfer = List[BoldApiObject]


class BoldApiConverter():

    """
    Converts from BOLD API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:

        self.__parser = parser

    def convert(self, input_: BoldApiTransfer) -> DataObject:
        """
        Converts a BoldApiTransfer containing a detail (single) result
        """
        return self.__parser.parse(input_)

    def convert_list(
        self,
        input_: BoldApiTransfer
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts a BoldApiTransfer containing a list of results. Also
        returns a count of the total results meeting.
        """

        return [
            self.__parser.parse(json_obj)
            for json_obj in input_
        ], len(input_)
