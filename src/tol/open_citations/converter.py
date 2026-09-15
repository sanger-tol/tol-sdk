# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, List, Optional

from .parser import Parser
from ..core import DataObject

OpenCitationsApiObject = dict[str, Any]
OpenCitationsApiTransfer = List[OpenCitationsApiObject]


class OpenCitationsApiConverter():

    """
    Converts from OpenCitations API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:

        self.__parser = parser

    def convert(
        self,
        object_type: str,
        input_: OpenCitationsApiObject
    ) -> DataObject:
        """
        Converts an OpenCitationsApiObject containing a detail (single) result.
        """
        return self.__parser.parse(object_type, input_)

    def convert_list(
        self,
        object_type: str,
        input_: OpenCitationsApiTransfer
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts an OpenCitationsApiTransfer containing a list of results. Also
        returns a count of the total number of results.
        """
        return [
            self.__parser.parse(object_type, json_obj)
            for json_obj in input_
            if json_obj is not None
        ], len(input_)
