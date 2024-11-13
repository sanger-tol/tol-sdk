# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional, Union

from .parser import Parser
from .view import View
from ..core import DataObject
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
        parser: Parser,
        data_key: str = 'data',
        meta_key: str = 'meta'
    ) -> None:

        self.__parser = parser
        self.__data_key = data_key
        self.__meta_key = meta_key

    def convert(self, input_: JsonApiTransfer) -> DataObject:
        """
        Converts a JsonApiTransfer containing a detail (single) result
        """

        json_obj = input_[self.__data_key]
        return self.__parser.parse(json_obj)

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
            self.__parser.parse(json_obj)
            for json_obj in json_obj_list
        ], total_count

    def convert_count(
        self,
        input_: JsonApiTransfer
    ) -> Dict[str, Any]:
        """
        Converts a JsonApiTransfer containing a list of stats.
        """

        stats = input_[self.__meta_key]
        return stats['total']

    def convert_stats(
        self,
        input_: JsonApiTransfer
    ) -> Dict[str, Any]:
        """
        Converts a JsonApiTransfer containing a list of stats.
        """

        stats = input_[self.__meta_key]
        return self.__parser.parse_stats(stats)

    def convert_group_stats(
        self,
        input_: JsonApiTransfer
    ) -> Dict[str, Any]:
        """
        Converts a JsonApiTransfer containing a list of grouped stats.
        """

        stats = input_[self.__meta_key]
        return self.__parser.parse_group_stats(stats)

    def convert_cursor_page(
        self,
        input_: JsonApiTransfer
    ) -> tuple[list[DataObject], list[str] | None]:
        """
        Converts a `JsonApiTransfer` of a cursor-page
        """

        objs = self.__parser.parse_iterable(
            input_[self.__data_key]
        )
        search_after = input_.get('meta', {}).get('search_after')

        return objs, search_after

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


class DataObjectConverter():

    """
    Converts from instances of `DataObject` to
    JSON:API transfers.
    """

    def __init__(self, view: View) -> None:
        self.__view = view

    def convert(self, input_: DataObject) -> JsonApiTransfer:
        """
        Converts a single `DataObject` instance to a JsonApiTransfer
        """

        return self.__view.dump(input_)

    def convert_list(self, input_: list[DataObject]) -> JsonApiTransfer:
        """
        Converts a `list` of `DataObject` instances to a JsonApiTransfer
        """

        return self.__view.dump_bulk(input_)
