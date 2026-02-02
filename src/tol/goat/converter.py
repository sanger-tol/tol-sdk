# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, List, Optional, Union

from .parser import Parser
from ..core import DataObject


GoatApiObject = dict[str, Any]
GoatApiTransfer = List[dict[
    str,
    Union[GoatApiObject, list[GoatApiObject]]
]]


class GoatApiConverter():

    """
    Converts from GoaT API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:

        self.__parser = parser

    def convert(self, input_: GoatApiTransfer) -> DataObject:
        """
        Converts a GoatApiTransfer containing a detail (single) result
        """
        return self.__parser.parse(input_)

    def convert_list(
        self,
        input_: GoatApiTransfer
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts a GoatApiTransfer containing a list of results. Also
        returns a count of the total results meeting.
        """

        return [
            self.__parser.parse(json_obj)
            for json_obj in input_
        ], len(input_)
