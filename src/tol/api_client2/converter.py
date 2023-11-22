# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional, Union

from tol.core import DataObject, DataObjectFactory

JsonApiObject = dict[str, Any]
JsonApiTransfer = dict[
    str,
    Union[JsonApiObject, list[JsonApiObject]]
]


class JsonApiConverter():

    """
    Converts from JSON:API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        data_object_factory: DataObjectFactory,
        data_key: str = 'data'
    ) -> None:

        self.__data_object_factory = data_object_factory
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

    def __convert_json_object(self, obj: JsonApiObject) -> DataObject:
        # TODO implement relationships recursively

        return self.__data_object_factory(
            obj['type'],
            obj.get('id'),
            data=obj.get('attributes')
        )


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
            json_obj['attributes'] = obj.attributes

        return json_obj
