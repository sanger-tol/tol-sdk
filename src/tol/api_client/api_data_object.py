# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from typing import Any, Dict

from ..core import DataDict, DataObject

if typing.TYPE_CHECKING:
    from .api_datasource import ApiDataSource


class ApiResponseDataObject(DataObject):
    """
    Used (internally) to marshall a JSON:API response
    into an inherited DataObject.
    """
    def __init__(
        self,
        data_source: ApiDataSource,
        json_api_response: Dict[str, Any],
        data: DataDict = None
    ):
        self.__data_source = data_source
        self.__json_api_response = json_api_response
        object_type = json_api_response['type']
        super().__init__(object_type, data)
