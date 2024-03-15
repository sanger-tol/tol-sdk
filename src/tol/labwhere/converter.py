# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional, Union

from .parser import Parser
from ..core import DataObject


LabwhereApiObject = dict[str, Any]
LabwhereApiTransfer = dict[
    str,
    Union[LabwhereApiObject, list[LabwhereApiObject]]
]


class LabwhereApiConverter():

    """
    Converts from LabWhere API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:

        self.__parser = parser

    def convert(self, input_: LabwhereApiTransfer) -> DataObject:
        """
        Converts a LabwhereApiTransfer containing a detail (single) result
        """

        return self.__parser.parse(input_)

    def convert_list(
        self,
        input_: LabwhereApiTransfer
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts a JsonApiTransfer containing a list of results. Also
        returns a count of the total results meeting.
        """

        return [
            self.__parser.parse(json_obj)
            for json_obj in input_
        ], len(input_)
