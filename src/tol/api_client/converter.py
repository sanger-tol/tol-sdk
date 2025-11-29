# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from .parser import Parser
from .view import DefaultView
from ..core import DataObject, DataSource, ReqFieldsTree
from ..core.relationship import RelationshipConfig


JsonApiObject = dict[str, Any]
JsonApiTransfer = dict[str, JsonApiObject | list[JsonApiObject]]
JsonRelationship = dict[
    str,  # "one" or "many"
    dict[str, str],  # relationship_name:target_type
]
JsonRelationshipConfig = dict[
    str,  # the object_type
    JsonRelationship,
]


class JsonApiConverter:
    """
    Converts from JSON:API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser,
    ) -> None:
        self.__parser = parser

    def convert(
        self,
        json_xfer: JsonApiTransfer,
    ) -> DataObject:
        """
        Converts a JsonApiTransfer containing a detail (single) result
        """

        obj_list = self.__parser.parse_json_doc(json_xfer)
        return obj_list[0] if obj_list else None

    def convert_list(
        self,
        json_xfer: JsonApiTransfer,
    ) -> tuple[list[DataObject], int | None]:
        """
        Converts a JsonApiTransfer containing a list of results. Also
        returns a count of the total results meeting.
        """

        objs = self.__parser.parse_json_doc(json_xfer)
        total_count = json_xfer.get('meta', {}).get('total', None)
        return objs, total_count

    def convert_count(
        self,
        json_xfer: JsonApiTransfer,
    ) -> dict[str, Any]:
        """
        Converts a JsonApiTransfer containing a list of stats.
        """

        stats = json_xfer['meta']
        return stats['total']

    def convert_stats(
        self,
        json_xfer: JsonApiTransfer,
    ) -> dict[str, Any]:
        """
        Converts a JsonApiTransfer containing a list of stats.
        """

        stats = json_xfer['meta']
        return self.__parser.parse_stats(stats)

    def convert_group_stats(
        self,
        json_xfer: JsonApiTransfer,
    ) -> dict[str, Any]:
        """
        Converts a JsonApiTransfer containing a list of grouped stats.
        """

        stats = json_xfer['meta']
        return self.__parser.parse_group_stats(stats)

    def convert_cursor_page(
        self,
        json_xfer: JsonApiTransfer,
    ) -> tuple[list[DataObject], list[str] | None]:
        """
        Converts a `JsonApiTransfer` of a cursor-page
        """

        objs = self.__parser.parse_json_doc(json_xfer)
        search_after = json_xfer.get('meta', {}).get('search_after')

        return objs, search_after

    def convert_relationship_config(
        self,
        config_transfer: JsonRelationshipConfig,
    ) -> dict[str, RelationshipConfig]:
        """
        Converts a `JsonRelationshipConfig` dict, returned from
        an `api_base2` config blueprint, to a form `ApiDataSource`
        can understand.
        """

        return {
            type_: self.__convert_relationship(rel)
            for type_, rel in config_transfer.items()
        }

    def __convert_relationship(
        self,
        rel: JsonRelationship,
    ) -> RelationshipConfig:
        return RelationshipConfig(
            to_one=rel.get('one'),
            to_many=rel.get('many'),
        )


class DataObjectConverter:
    """
    Converts from instances of `DataObject` to
    JSON:API transfers.
    """

    def __init__(
        self,
        data_source: DataSource,
        prefix: str | None = None,
    ) -> None:
        self.__data_source = data_source
        self.__prefix = prefix

    def __build_view(self, object_type):
        req_fields_tree = ReqFieldsTree(object_type, self.__data_source)
        return DefaultView(req_fields_tree, self.__prefix)

    def convert(self, data_obj: DataObject) -> JsonApiTransfer:
        """
        Converts a single `DataObject` instance to a JsonApiTransfer
        """

        view = self.__build_view(data_obj.type)
        return view.dump(data_obj)

    def convert_list(self, data_obj_list: list[DataObject]) -> JsonApiTransfer:
        """
        Converts a `list` of `DataObject` instances to a JsonApiTransfer
        """

        if not data_obj_list:
            msg = 'Cannot convert empty list'
            raise ValueError(msg)
        view = self.__build_view(data_obj_list[0].type)
        return view.dump_bulk(data_obj_list)
