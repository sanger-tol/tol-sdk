# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Optional

import requests


ObjectDump = dict[str, Any]


class ApiClient(ABC):
    """Makes requests to a remote API"""

    @abstractmethod
    def get_detail(self, type_: str, id_: str) -> ObjectDump:
        """
        Gets the dict-dump of a `DataObject` with the
        specified type and ID.
        """

    @abstractmethod
    def get_page(
        self,
        type_: str,
        page_number: int,
        page_size: Optional[int],
        filters: Optional[dict[str, Any]],
        sort_by: Optional[str]
    ) -> list[ObjectDump]:
        """
        Gets the page of results, sorted as specified,
        matching the given filters.
        """


class DefaultApiClient(ApiClient):

    def __init__(self, url: str, token: str) -> None:
        super().__init__()

    def get_detail(self, type_: str, id_: str) -> ObjectDump:
        pass

    def get_page(
        self,
        type_: str,
        page_number: int,
        page_size: Optional[int],
        filters: Optional[dict[str, Any]],
        sort_by: Optional[str]
    ) -> list[ObjectDump]:

        pass
