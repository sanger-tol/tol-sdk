# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from typing import Any, Dict, List

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
        self.__init_relationships()
        object_type = json_api_response['type']
        super().__init__(object_type, data)

    def __init_relationships(self) -> None:
        self.__relationships = self.__json_api_response.get(
            'relationships',
            {}
        )
        for relationship in self.__relationships:
            v = property(
                lambda : self.__get_relationship_link(relationship)
            )
            setattr(
                self,
                relationship,
                v
            )
        
    def __get_relationship_link(
        self,
        relationship: str
    ) -> ApiResponseDataObject:
        pass
