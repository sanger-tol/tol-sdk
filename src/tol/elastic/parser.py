# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime
from dataclasses import dataclass
from collections.abc import Callable, Iterable, Mapping
from typing import Any, TYPE_CHECKING

import dateutil

from .filter import ElasticFilterConverter
from ..core import DataObject, DataSourceFilter, DataSourceParser

if TYPE_CHECKING:
    from . import ElasticDataSource


ElasticApiResource = dict[str, Any]


@dataclass(slots=True)
class ElasticUpsertInputResource:
    index: str
    objects: Iterable[DataObject]
    id_func: Callable
    field_prefix: str


@dataclass(slots=True)
class ElasticUpdateInputResource:
    object_type: str
    update: dict
    field_prefix: str
    candidate_key: Iterable[str]


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


class _ToElasticApiResourceParser:
    def _convert_dates(self, dict_: dict) -> dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, datetime.datetime):
                ret[k] = v.isoformat()
            else:
                ret[k] = v
        return ret

    @property
    def _update_script(self):
        s = """
            for (param in params['upsertWith'].entrySet()) {
                if (param.value != null) {
                    if (ctx._source[param.key] instanceof Map) {
                        for (newParam in param.value.entrySet()) {
                            ctx._source[param.key][newParam.key] = newParam.value;
                        }
                        continue
                    }
                    if (ctx._source[param.key] instanceof ArrayList) {
                        for (newParam in param.value) {
                            if(! ctx._source[param.key].contains(newParam)) {
                                ctx._source[param.key].add(newParam)
                            }
                        }
                        continue
                    }
                }
                ctx._source[param.key] = param.value;
            }
        """
        return s.replace('\n', ' ')

    @property
    def _upsert_script(self):
        s = f"""
            if ( ctx.op == 'create' ) {{
                ctx._source = params['upsertWith']
            }} else {{
                {self._update_script}
            }}
        """
        return s.replace('\n', ' ')

    def _prefix_fields(self, dict_: dict, prefix: str) -> dict:
        if prefix == '':
            return dict_
        ret = {}
        for k, v in dict_.items():
            ret[prefix + '_' + k] = v
        return ret

    def _parse_to_one_relation(
        self,
        one_relation: DataObject | None
    ) -> dict[str, Any] | None:

        if one_relation is None:
            return None

        return {
            'id': one_relation.id,
            **one_relation.attributes
        }


class DefaultDataObjectParser(
    DataSourceParser[ElasticUpsertInputResource, ElasticApiResource],
    _ToElasticApiResourceParser
):
    __slots__ = ['__data_source']
    __data_source: ElasticDataSource

    def __init__(self, data_source: ElasticDataSource) -> None:
        self.__data_source = data_source

    def parse(
        self,
        transfer: ElasticUpsertInputResource,
    ):
        real_index_name = self.__data_source._get_indices().get(transfer.index)
        for object_ in transfer.objects:
            obj = self._convert_data_object_to_dict(object_)
            obj = self._convert_dates(obj)
            obj = self._prefix_fields(obj, transfer.field_prefix)
            obj = self._stringify_ids(obj)
            uid = transfer.id_func(object_)
            obj = self._add_uid(obj, uid)
            yield {
                '_op_type': 'update',
                'scripted_upsert': True,
                'upsert': {},
                '_index': real_index_name,
                '_id': uid,
                'script': {
                    'source': self._upsert_script,
                    'lang': 'painless',
                    'params': {
                        'upsertWith': obj
                    }
                }
            }

    def _convert_data_object_to_dict(self, data_object: DataObject) -> dict:
        to_ones_dict = {
            k: self._parse_to_one_relation(v)
            for k, v in data_object._to_one_objects.items()
        }
        return data_object.attributes | to_ones_dict

    def _stringify_ids(self, dict_: dict) -> dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, dict):
                if 'id' in v:
                    v['id'] = str(v['id'])
                ret[k] = self._stringify_ids(v)
            else:
                ret[k] = v

        return ret

    def _add_uid(self, dict_: dict, uid: Any) -> dict:
        return {**dict_, 'uid': f'{uid}'}


class DefaultDataObjectUpdateParser(
    DataSourceParser[ElasticUpdateInputResource, ElasticApiResource],
    _ToElasticApiResourceParser
):
    __slots__ = ['__data_source']
    __data_source: ElasticDataSource

    def __init__(self, data_source: ElasticDataSource) -> None:
        self.__data_source = data_source

    def parse(
        self,
        transfer: ElasticUpdateInputResource,
    ):
        u = self._convert_dates(transfer.update)
        f = DataSourceFilter()
        f.and_ = {}
        for key in transfer.candidate_key:
            # Don't want key in the upsert as it cannot change anyway
            f.and_[key] = {'eq': {'value': u.pop(key)}}
        u = self._prefix_fields(u, transfer.field_prefix)
        u = self._convert_data_objects_in_update_to_dict(u)
        query = ElasticFilterConverter(self.__data_source).convert(
            transfer.object_type, object_filters=f
        )
        return {
            'query': query,
            'script': {
                'source': self._update_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': u
                }
            },
        }

    def _convert_data_objects_in_update_to_dict(self, dict_: dict) -> dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, DataObject):
                ret[k] = self._parse_to_one_relation(v)
            else:
                ret[k] = v
        return ret
