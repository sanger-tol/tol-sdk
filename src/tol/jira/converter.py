# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, List, Optional

from .parser import Parser
from ..core import DataObject


JiraIssue = dict[str, Any]
JiraIssues = List[JiraIssue]


class JiraConverter():

    """
    Converts from Jira transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:

        self.__parser = parser

    def convert(self, input_: JiraIssue) -> DataObject:
        """
        Converts a JiraIssue containing a detail (single) result
        """
        return self.__parser.parse(input_)

    def convert_list(
        self,
        input_: JiraIssues
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts a JiraIssues containing a list of results. Also
        returns a count of the total results meeting.
        """

        return [
            self.__parser.parse(issue)
            for issue in input_
        ], len(input_)
