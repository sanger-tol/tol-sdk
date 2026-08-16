# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

import dateutil

from .elastic_utils import ElasticUtils
from .filter import ElasticFilterConverter
from .runtime_fields import RuntimeFields
from ..core import DataObject, DataSourceFilter, DataSourceParser

if TYPE_CHECKING:
    from . import ElasticDataSource


ElasticApiResource = dict[str, Any]


@dataclass(slots=True)
class ElasticUpsertInputResource:
    index: str
    objects: Iterable[DataObject]
    id_func: Callable
    provenance: str | None = None


@dataclass(slots=True)
class ElasticUpdateInputResource:
    object_type: str
    update: dict
    candidate_key: Iterable[str]
    provenance: str | None = None


class DefaultElasticApiParser(DataSourceParser[ElasticApiResource, DataObject]):
    """
    Parses Elastic API transfer resource `dict`s to `DataObject` instances
    """
    __slots__ = ['_data_source']
    _data_source: ElasticDataSource

    def __init__(self, data_source: ElasticDataSource) -> None:
        self._data_source = data_source

    def parse(self, transfer: ElasticApiResource) -> DataObject | None:
        if '_source' in transfer:
            type_ = self._data_source._real_index_to_object_type(transfer['_index'])
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
        direct_provenance_attrs = {
            k for k in self._data_source.provenance_fields.get(type_, {})
            if not k.endswith('.id')
        }

        attributes = {
            k: self.__make_dates(type_, k, v) for k, v in data.items()
            if k in self._data_source.attribute_types[type_]
            and k not in direct_provenance_attrs
        }
        runtime_attributes = {
            k: self.__make_dates(type_, k, v[0]) for k, v in runtime_data.items()
            if k in self._data_source.attribute_types[type_]
        }
        provenanced_attributes = {
            ElasticUtils.actual_attribute(k): self.__make_dates(
                type_,
                ElasticUtils.actual_attribute(k),
                self.__normalise_runtime_value(v[0]),
            )
            for k, v in runtime_data.items()
            if type_ in self._data_source.provenance_fields
            and ElasticUtils.actual_attribute(k) in self._data_source.provenance_fields[type_]
            and ElasticUtils.actual_attribute(k) in self._data_source.attribute_types[type_]
        }

        for attr_name in direct_provenance_attrs:
            if (
                attr_name in self._data_source.attribute_types.get(type_, {})
                and attr_name not in provenanced_attributes
            ):
                provenanced_attributes[attr_name] = None

        to_one = self.__make_to_one_relations(type_, data, runtime_data)
        provenance = self.__make_provenances(type_, data)
        return self._data_source.data_object_factory(
            type_,
            id_=id_,
            attributes=attributes | runtime_attributes | provenanced_attributes,
            to_one=to_one,
            provenance_=provenance
        )

    def __make_provenances(self, type_: str, data: dict[str, Any]) -> dict[str, DataObject | None]:
        if type_ not in self._data_source.provenance_fields:
            return {}

        # This picks out the relationships that have provenance
        relationships_with_provenance = {
            k: self.__make_provenance_for_relationship(v, type_) for k, v in data.items()
            if f'{k}.id' in self._data_source.provenance_fields[type_]
        }

        # This picks out all the direct attributes that have provenance
        attributes_with_provenance = {
            k: {
                source: self.__make_dates(
                    type_,
                    k,
                    self.__normalise_runtime_value(details['value']),
                )
                for source, details in v['provenance'].items()
            }
            for k, v in data.items()
            if k in self._data_source.provenance_fields[type_]
            and k not in relationships_with_provenance
            and v is not None
            and isinstance(v, dict)
            and 'provenance' in v
        }

        return attributes_with_provenance | relationships_with_provenance

    def __make_provenance_for_relationship(
        self,
        relation_data: dict[str, Any] | None, type_: str
    ) -> str | None:
        if (
            relation_data is None
            or not isinstance(relation_data, Mapping)
        ):
            return None

        id_ = relation_data.get('id')

        if id_ is None:
            return None

        if isinstance(id_, dict) and 'provenance' in id_:
            result = {}
            for source in id_.get('provenance', {}):
                source_id = self.__normalise_runtime_value(id_['provenance'][source]['value'])
                if source_id is None:
                    result[source] = None
                    continue
                result[source] = self._convert_data_dict_to_data_object(
                    type_,
                    source_id,
                    relation_data,
                    {}
                )
            return result

        return self._convert_data_dict_to_data_object(
            type_,
            id_,
            relation_data,
            {},  # This can be empty because runtime_fields are not applicable for enriched objects
        )

    def __make_dates(self, object_type, attribute_name, value):
        if self._data_source.attribute_types[object_type][attribute_name] == 'datetime' and \
                isinstance(value, str):
            return dateutil.parser.parse(value)
        return value

    def __make_to_one_relations(
        self,
        type_: str,
        data: dict[str, Any],
        runtime_data: dict[str, Any] = None
    ) -> dict[str, DataObject | None]:

        if type_ not in self._data_source.relationship_config:
            return {}

        if self._data_source.relationship_config[type_].to_one is None:
            return {}

        return {
            k: self.__make_to_one_relation(
                relation_name=k,
                relation_data=data.get(k),
                parent_type=type_,
                child_type=v,
                runtime_data=runtime_data
            )
            for k, v in self._data_source.relationship_config[type_].to_one.items()
        }

    def __make_to_one_relation(
        self,
        relation_name: str,
        relation_data: dict[str, Any] | None,
        parent_type: str,
        child_type: str,
        runtime_data: dict[str, Any] = None
    ) -> DataObject | None:

        if (
            relation_data is None
            or not isinstance(relation_data, Mapping)
        ):
            return None

        id_ = relation_data.get('id')
        # If this relation is provenanced, we need to get the id from the runtime fields
        if parent_type in self._data_source.provenance_fields and \
                f'{relation_name}.id' in self._data_source.provenance_fields[parent_type] and \
                runtime_data is not None and \
                f'{relation_name}.id.value' in runtime_data:
            id_ = self.__normalise_runtime_value(runtime_data[f'{relation_name}.id.value'][0])

        if id_ is None:
            return None
        if isinstance(id_, dict):
            raise ValueError(
                f'Unexpected dict for id of relation {relation_name} '
                f'in {parent_type}: {id_}. '
                f'provenance_fields={self._data_source.provenance_fields[parent_type]}'
                f' runtime_fields={runtime_data}'
            )

        return self._convert_data_dict_to_data_object(
            child_type,
            id_,
            relation_data,
            {},  # This can be empty because runtime_fields are not applicable for enriched objects
        )

    def __normalise_runtime_value(self, value: Any) -> Any:
        if value == RuntimeFields.NULL_SENTINEL:
            return None
        return value


class _ToElasticApiResourceParser:
    def __should_use_null_sentinel(self, object_type: str, provenance_field: str) -> bool:
        if (
            object_type not in self._data_source.provenance_fields
            or provenance_field not in self._data_source.provenance_fields[object_type]
        ):
            return False

        field_cfg = self._data_source.provenance_fields[object_type][provenance_field]
        return (field_cfg.return_type or 'keyword') == 'keyword'

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
                            if (newParam.value instanceof Map
                                    && ctx._source[param.key][newParam.key] instanceof Map) {
                                for (innerParam in newParam.value.entrySet()) {
                                    if (innerParam.value instanceof Map
                                            && ctx._source[param.key][newParam.key]
                                            [innerParam.key] instanceof Map) {
                                        for (deepParam in innerParam.value.entrySet()) {
                                            ctx._source[param.key][newParam.key]
                                            [innerParam.key][deepParam.key] = deepParam.value;
                                        }
                                    } else {
                                        ctx._source[param.key][newParam.key][innerParam.key]
                                            = innerParam.value;
                                    }
                                }
                            } else {
                                ctx._source[param.key][newParam.key] = newParam.value;
                            }
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

    def _parse_attribute(
        self,
        object_type: str,
        name: str,
        value: Any | None,
        provenance: str | None,
    ) -> dict[str, Any] | None:
        if provenance is not None and \
                object_type in self._data_source.provenance_fields and \
                name in self._data_source.provenance_fields[object_type]:
            parsed_value = value
            if value is None and self.__should_use_null_sentinel(object_type, name):
                parsed_value = RuntimeFields.NULL_SENTINEL
            return {
                'provenance': {
                    provenance: {'value': parsed_value}
                }
            }

        if value is None:
            return None

        return value

    def _parse_to_one_relation(
        self,
        object_type: str,
        name: str,
        one_relation: DataObject | None,
        provenance: str | None,
    ) -> dict[str, Any] | None:

        if one_relation is None:
            if provenance is not None and \
                    object_type in self._data_source.provenance_fields and \
                    f'{name}.id' in self._data_source.provenance_fields[object_type]:
                parsed_value = None
                if self.__should_use_null_sentinel(object_type, f'{name}.id'):
                    parsed_value = RuntimeFields.NULL_SENTINEL
                return {
                    'id': {
                        'provenance': {
                            provenance: {'value': parsed_value}
                        }
                    }
                }
            return None

        if provenance is not None and \
                object_type in self._data_source.provenance_fields and \
                f'{name}.id' in self._data_source.provenance_fields[object_type]:
            return {
                'id': {
                    'provenance': {
                        provenance: {'value': one_relation.id}
                    }
                },
                **one_relation.attributes
            }

        return {
            'id': one_relation.id,
            **one_relation.attributes
        }


class DefaultElasticUpsertInputParser(
    DataSourceParser[ElasticUpsertInputResource, ElasticApiResource],
    _ToElasticApiResourceParser
):
    __slots__ = ['_data_source']
    _data_source: ElasticDataSource

    def __init__(self, data_source: ElasticDataSource) -> None:
        self._data_source = data_source

    def parse(
        self,
        transfer: ElasticUpsertInputResource,
    ):
        real_index_name = self._data_source._get_indices().get(transfer.index)
        for object_ in transfer.objects:
            obj = self._convert_data_object_to_dict(object_, transfer.provenance)
            obj = self._convert_dates(obj)
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

    def _convert_data_object_to_dict(
        self,
        data_object: DataObject,
        provenance: str | None,
    ) -> dict:
        attributes_dict = {
            k: self._parse_attribute(data_object.type, k, v, provenance)
            for k, v in data_object.attributes.items()
        }
        to_ones_dict = {
            k: self._parse_to_one_relation(data_object.type, k, v, provenance)
            for k, v in data_object._to_one_objects.items()
        }
        return attributes_dict | to_ones_dict

    def _stringify_ids(self, dict_: dict) -> dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, dict):
                if (
                    'id' in v
                    and isinstance(v['id'], dict)
                    and 'provenance' in v['id']
                ):
                    v['id'] = {
                        'provenance': {
                            source: {**details, 'value': str(details['value'])}
                            for source, details in v['id']['provenance'].items()
                        }
                    }
                ret[k] = self._stringify_ids(v)
            else:
                ret[k] = v

        return ret

    def _add_uid(self, dict_: dict, uid: Any) -> dict:
        return {**dict_, 'uid': f'{uid}'}


class DefaultElasticUpdateInputParser(
    DataSourceParser[ElasticUpdateInputResource, ElasticApiResource],
    _ToElasticApiResourceParser
):
    __slots__ = ['_data_source']
    _data_source: ElasticDataSource

    def __init__(self, data_source: ElasticDataSource) -> None:
        self._data_source = data_source

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
        u = self._convert_data_objects_in_update_to_dict(
            transfer.object_type, u, transfer.provenance
        )
        query = ElasticFilterConverter(self._data_source).convert(
            transfer.object_type, object_filters=f
        )
        runtime_mappings = (
            dict(self._data_source.runtime_fields[transfer.object_type])
            if transfer.object_type in self._data_source.runtime_fields
            else None
        )
        payload = {
            'query': query,
            'script': {
                'source': self._update_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': u
                }
            },
        }
        if runtime_mappings is not None:
            payload['runtime_mappings'] = runtime_mappings
        return payload

    def _convert_data_objects_in_update_to_dict(
        self, object_type: str, dict_: dict, provenance: str | None
    ) -> dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, DataObject):
                ret[k] = self._parse_to_one_relation(object_type, k, v, provenance)
            else:
                ret[k] = self._parse_attribute(object_type, k, v, provenance)
        return ret
