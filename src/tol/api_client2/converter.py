# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime
from typing import Any, Optional, Union

from ..core import DataObject, DataSource
from ..core.relationship import RelationshipConfig


JsonApiObject = dict[str, Any]
JsonApiTransfer = dict[
    str,
    Union[JsonApiObject, list[JsonApiObject]]
]
JsonRelationship = dict[
    str,  # "one" or "many"
    dict[str, str]  # relationship_name:target_type
]
JsonRelationshipConfig = dict[
    str,  # the object_type
    JsonRelationship
]


class JsonApiConverter():

    """
    Converts from JSON:API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        data_source: DataSource,
        data_key: str = 'data'
    ) -> None:

        self.__data_source = data_source
        self.__data_key = data_key

    def convert(self, input_: JsonApiTransfer) -> DataObject:
        """
        Converts a JsonApiTransfer containing a detail (single) result
        """

        json_obj = input_[self.__data_key]
        return self.__convert_json_object(json_obj)

    def convert_list(
        self,
        input_: JsonApiTransfer
    ) -> tuple[list[DataObject], Optional[int]]:
        """
        Converts a JsonApiTransfer containing a list of results. Also
        returns a count of the total results meeting.
        """

        json_obj_list = input_[self.__data_key]
        total_count = input_.get('meta', {}).get('total', None)
        return [
            self.__convert_json_object(json_obj)
            for json_obj in json_obj_list
        ], total_count

    def convert_relationship_config(
        self,
        config_transfer: JsonRelationshipConfig
    ) -> dict[str, RelationshipConfig]:
        """
        Converts a `JsonRelationshipConfig` dict, returned from
        an `api_base2` config blueprint, to a form `ApiDataSource`
        can understand.
        """

        return {
            type_: self.__convert_relationship(rel)
            for type_, rel
            in config_transfer.items()
        }

    def __convert_relationship(
        self,
        rel: JsonRelationship
    ) -> RelationshipConfig:

        return RelationshipConfig(
            to_one=rel.get('one'),
            to_many=rel.get('many')
        )

    def __convert_json_object(self, obj: JsonApiObject) -> DataObject:
        # TODO implement relationships recursively

        type_ = obj['type']

        attributes = self.__convert_attributes(
            type_,
            obj.get('attributes')
        )

        return self.__data_source.data_object_factory(
            type_,
            obj.get('id'),
            attributes=attributes
        )

    def __convert_attributes(
        self,
        type_: str,
        attributes: Optional[dict[str, Any]]
    ) -> dict[str, Any]:

        if not attributes:
            return {}

        datetime_keys = self.__get_datetime_keys(type_)

        return {
            k: datetime.fromisoformat(v) if k in datetime_keys else v
            for k, v in attributes.items()
        }

    def __get_datetime_keys(self, type_: str) -> list[str]:
        attribute_types = self.__data_source.attribute_types.get(
            type_,
            {}
        )

        return [
            k for k, v in attribute_types.items()
            if self.__value_is_datetime(v)
        ]

    def __value_is_datetime(self, __v: str) -> bool:
        lower_ = __v.lower()

        return 'date' in lower_ or 'time' in lower_


class DataObjectConverter():

    """
    Converts from instances of `DataObject` to
    JSON:API transfers.
    """

    def __init__(self, data_key: str = 'data') -> None:
        self.__data_key = data_key

    def convert(self, input_: DataObject) -> JsonApiTransfer:
        """
        Converts a single `DataObject` instance to a JsonApiTransfer
        """

        return {
            self.__data_key: self.__convert_data_object(input_)
        }

    def convert_list(self, input_: list[DataObject]) -> JsonApiTransfer:
        """
        Converts a `list` of `DataObject` instances to a JsonApiTransfer
        """

        return {
            self.__data_key: [
                self.__convert_data_object(obj)
                for obj in input_
            ]
        }

    def __convert_data_object(self, obj: DataObject) -> JsonApiObject:
        # TODO support relationships

        json_obj = {
            'type': obj.type
        }

        return self.__add_optional_fields(obj, json_obj)

    def __add_optional_fields(
        self,
        obj: DataObject,
        json_obj: JsonApiObject
    ) -> JsonApiObject:

        if obj.id is not None:
            json_obj['id'] = obj.id

        if obj.attributes:
            json_obj['attributes'] = self.__convert_attributes(
                obj.attributes
            )

        return json_obj

    def __convert_attributes(
        self,
        attributes: dict[str, Any]
    ) -> dict[str, Any]:

        return {
            k: self.__convert_value(v)
            for k, v in attributes.items()
        }

    def __convert_value(self, __v: Any) -> Any:
        if isinstance(__v, (date, datetime)):
            return __v.isoformat()
        return __v
