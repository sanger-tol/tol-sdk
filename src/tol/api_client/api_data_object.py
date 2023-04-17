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
        object_type: str,
        data_source: ApiDataSource,
        data: DataDict = None
    ):
        self.__data_source = data_source
        t_cache = Dict[str, Dict[str, ApiResponseDataObject]]
        self.__relationship_cache: t_cache = {}
        super().__init__(object_type, data)
        
    def get_relationship_link(
        self,
        relationship: Dict[str, Any]
    ) -> ApiResponseDataObject:
        object_id = relationship['id']
        object_type = relationship['type']
        cached = self.__get_cached_relation(object_type, object_id)
        if cached is not None:
            return cached
        else:
            return self.__data_source.get_by_id(
                object_type,
                [object_id]
            )[0]

    def __get_cached_relation(
        self,
        relationship: str,
        object_id: str
    ) -> ApiResponseDataObject:
        return self.__relationship_cache.get(
            relationship,
            {}
        ).get(object_id)


def __new_lambda(relationship_value: Dict[str, Any]) -> Any:
    return lambda s: s.get_relationship_link(
        relationship_value.get('data', {})
    )

def __new_class(relationships: Dict[str, Any]) -> object:
    return type(
        '',
        (ApiResponseDataObject,),
        {
            r: property(__new_lambda(v))
            for r, v in relationships.items()
        }
    )


def new_api_response_data_object(
    data_source: ApiDataSource,
    json_api_response: Dict[str, Any],
    data: DataDict = None
) -> ApiResponseDataObject:
    """
    Creates a new ApiResponseDataObject with the specified
    relationship properties
    """
    relationships = json_api_response.get('relationships', {})
    new_class = __new_class(relationships)
    object_type = json_api_response.get('type')
    return new_class(
        object_type,
        data_source,
        data
    )
