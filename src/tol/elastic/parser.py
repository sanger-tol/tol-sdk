# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TYPE_CHECKING

import dateutil

from ..core import DataObject, DataSourceParser

if TYPE_CHECKING:
    from . import ElasticDataSource


ElasticApiResource = dict[str, Any]


class DefaultElasticApiParser(DataSourceParser[ElasticApiResource, DataObject]):
    """
    Parses Elastic API transfer resource `dict`s to `DataObject` instances
    """
    __slots__ = ['__data_source']
    __data_source: ElasticDataSource

    def __init__(self, data_source: ElasticDataSource) -> None:
        self.__data_source = data_source

    def parse(self, transfer: ElasticApiResource) -> DataObject | None:
        if '_source' in transfer:
            type_ = self.__data_source._real_index_to_object_type(transfer['_index'])
            id_ = transfer['_id']
            attributes = transfer['_source']
            runtime_attributes = transfer['fields'] if 'fields' in transfer else {}
            return self._convert_data_dict_to_data_object(
                type_,
                id_,
                attributes,
                runtime_attributes
            )
        else:
            return None

    def _convert_data_dict_to_data_object(self, type_, id_, data, runtime_data):
        attributes = {
            k: self.__make_dates(type_, k, v) for k, v in data.items()
            if k in self.__data_source.attribute_types[type_]
        }
        runtime_attributes = {
            k: self.__make_dates(type_, k, v[0]) for k, v in runtime_data.items()
            if k in self.__data_source.attribute_types[type_]
        }
        to_one = self.__make_to_one_relations(type_, data)
        return self.__data_source.data_object_factory(
            type_,
            id_=id_,
            attributes=attributes | runtime_attributes,
            to_one=to_one
        )

    def __make_dates(self, object_type, attribute_name, value):
        if self.__data_source.attribute_types[object_type][attribute_name] == 'datetime' and \
                isinstance(value, str):
            return dateutil.parser.parse(value)
        return value

    def __make_to_one_relations(
        self,
        type_: str,
        data: dict[str, Any]
    ) -> dict[str, DataObject | None]:

        if type_ not in self.__data_source.relationship_config:
            return {}

        if self.__data_source.relationship_config[type_].to_one is None:
            return {}

        return {
            k: self.__make_to_one_relation(data.get(k), v)
            for k, v in self.__data_source.relationship_config[type_].to_one.items()
        }

    def __make_to_one_relation(
        self,
        relation_data: dict[str, Any] | None,
        type_: str
    ) -> DataObject | None:

        if (
            relation_data is None
            or not isinstance(relation_data, Mapping)
        ):
            return None

        id_ = relation_data.get('id')

        if id_ is None:
            return None

        return self._convert_data_dict_to_data_object(
            type_,
            id_,
            relation_data,
            {}  # This can be empty because runtime_fields are not applicable for enriched objects
        )


class DefaultDataObjectParser(DataSourceParser[DataObject, ElasticApiResource]):
    def parse(self, transfer: DataObject) -> ElasticApiResource:
        raise NotImplementedError
