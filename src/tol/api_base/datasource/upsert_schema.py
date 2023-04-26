# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Set

from marshmallow import (
    Schema,
    fields,
    post_load,
    validates_schema,
    ValidationError
)

from .api_upsert_object import ApiUpsertObject
from ...core import DataObject


UpsertData = Dict[str, List[Dict[str, Any]]]


class UpsertRelationshipSchema(Schema):
    one = fields.Dict(
        keys=fields.String(),
        values=fields.String()
    )

    many = fields.Dict(
        keys=fields.String(),
        values=fields.List(
            fields.String()
        )
    )


class UpsertObjectSchema(Schema):
    _uuid = fields.String(required=True)
    type = fields.String(required=True)  # noqa
    id = fields.String()  # noqa
    attributes = fields.Dict()
    relationships = fields.Nested(UpsertRelationshipSchema)


class UpsertSchema(Schema):
    data = fields.List(fields.Nested(UpsertObjectSchema))

    @post_load
    def __parse_data_objects(
        self,
        upsert_data: UpsertData,
        **kwargs
    ) -> List[DataObject]:
        upsert_list = upsert_data.get('data', [])
        upsert_objects = self.__parse_api_upsert_objects(upsert_list)
        self.__uuid_map = self.__create_uuid_map(upsert_objects)
        return self.__process_upsert_list(upsert_objects)

    @validates_schema
    def __validate_relationship_uuids(
        self,
        upsert_data: UpsertData,
        **kwargs
    ) -> None:
        pass

    def __get_uuid_set(
        self,
        upsert_data: UpsertData
    ) -> Set[str]:
        upsert_list = upsert_data.get('data', [])
        self.__uuid_set = {
            u.get('_uuid') for u in upsert_list
        }
        self.__uuid_set.discard(None)
        return upsert_data

    def __process_upsert_list(
        self,
        upsert_objects: List[ApiUpsertObject]
    ) -> List[DataObject]:
        for upsert_object in upsert_objects:
            self.__process_api_upsert_object(upsert_object)
        return upsert_objects

    def __parse_api_upsert_objects(
        self,
        upsert_list: List[Dict[str, Any]]
    ) -> List[ApiUpsertObject]:

        return [
            ApiUpsertObject(json_dict)
            for json_dict in upsert_list
        ]

    def __create_uuid_map(
        self,
        api_upsert_objects: List[ApiUpsertObject]
    ) -> Dict[str, ApiUpsertObject]:

        return {
            u._internal_uuid: u
            for u in api_upsert_objects
        }

    def __process_api_upsert_object(
        self,
        upsert_object: ApiUpsertObject
    ) -> None:
        self.__process_all_to_ones(upsert_object)
        self.__process_all_to_manys(upsert_object)

    def __process_all_to_ones(
        self,
        upsert_object: ApiUpsertObject
    ) -> None:
        for name, one_uuid in upsert_object._to_one_uuids.items():
            one_object = self.__get_object_by_uuid(one_uuid)
            upsert_object.add_to_one_relationship_object(name, one_object)

    def __process_all_to_manys(
        self,
        upsert_object: ApiUpsertObject
    ) -> None:
        for name, many_uuids in upsert_object._to_many_uuids.items():
            for __uuid in many_uuids:
                many_object = self.__get_object_by_uuid(__uuid)
                upsert_object.add_to_many_relationship_object(
                    name,
                    many_object
                )

    def __get_object_by_uuid(self, __uuid: str) -> ApiUpsertObject:
        api_upsert_object = self.__uuid_map[__uuid]
        return api_upsert_object
