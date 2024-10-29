# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, List, Optional, Union

from .parser import Parser
from ..core import DataObject

EnaApiObject = dict[str, Any]
EnaApiTransfer = List[dict[
    str,
    Union[EnaApiObject, list[EnaApiObject]]
]]


class EnaApiConverter():
    """
    Converts from ENA API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:

        self.__parser = parser

    def convert(self, input_: EnaApiTransfer) -> DataObject:
        """
        Convert an EnaApiTransfer containing a detail (single) result.
        """
        return self.__parser.parse(input_)

    def convert_list(
        self,
        object_type: str,
        input_: EnaApiTransfer
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts an EnaApiTransfer containing a list of results. Also
        returns a count of the total number of results.
        """
        return [
            self.__parser.parse(object_type, json_obj)
            for json_obj in input_
        ], len(input_)
