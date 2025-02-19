# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from ...api_client.exception import BaseRuntimeException


Data = Union[
    dict[str, Any],
    list[dict[str, Any]]
]
Errors = list[dict[str, Any]]


class RequestBody(ABC):
    """A useful wrapper around a request body"""

    @property
    @abstractmethod
    def data(self) -> Optional[Data]:
        """Under the 'data' key"""

    @property
    @abstractmethod
    def meta(self) -> Optional[dict[str, Any]]:
        """Under the 'meta' key"""

    @property
    @abstractmethod
    def errors(self) -> Optional[Errors]:
        """Under the 'errors' key"""


class JsonApiRequestBody(RequestBody):
    """Implements RequestBody for a JSON:API body"""

    def __init__(self, json_dict: dict[str, Any]) -> None:
        self.__json = json_dict

    @property
    def data(self) -> Optional[Data]:
        if self.errors is not None:
            raise BaseRuntimeException(
                errors=[{
                    'title': 'Error Response Received',
                    'detail': json.dumps(self.errors)
                }]
            )
        return self.__json.get('data', {})

    @property
    def meta(self) -> Optional[dict[str, Any]]:
        return self.__json.get('meta')

    @property
    def errors(self) -> Optional[Errors]:
        return self.__json.get('errors')
