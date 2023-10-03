# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from functools import cache
from typing import Any, Dict, Iterable, Optional, Tuple

from caseconverter import (
    kebabcase,
    snakecase
)

from dateutil import parser

from elasticsearch import (Elasticsearch, helpers)

from ..core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import (
    Aggregator,
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
)
from ..core.operator.updater import DataObjectUpdate
from ..core.relationship import (
    RelationshipConfig
)


class ElasticDataSource(
    DataSource,
    DetailGetter,
    PageGetter,
    ListGetter,
    Aggregator,
    Relational,
    Updater,
    Upserter
):

    def __init__(self, config: Dict):
        super().__init__(config, expected=['uri', 'user', 'password',
                                           'index_prefix', 'relationship_cfg'])
        """
        relationship_cfg is also supported if we want to handle relationships
        Only FKs pointing to IDs are currently supported
        """
        self._initialise_elasticsearch()

    def _initialise_elasticsearch(self):
        self.es = Elasticsearch(self.uri, http_auth=(self.user, self.password))
        self.helpers = helpers

    def _convert_data_object_to_dict(self, data_object: DataObject) -> Dict:
        return data_object.attributes

    def _prefix_fields(self, dict_: Dict, prefix: str) -> Dict:
        if prefix == '':
            return dict_
        ret = {}
        for k, v in dict_.items():
            ret[prefix + '_' + k] = v
        return ret

    def _add_updated(self, dict_: Dict) -> Dict:
        return {**dict_, 'tol_updated_at': datetime.now().isoformat()}

    def _add_checksum(self, dict_: Dict) -> Dict:
        dhash = hashlib.sha256()
        encoded = json.dumps(dict_, sort_keys=True, default=str).encode()
        dhash.update(encoded)
        return {**dict_, 'checksum': dhash.hexdigest()}

    def _add_uid(self, dict_: Dict, uid: Any) -> Dict:
        return {**dict_, 'uid': f'{uid}'}

    def _convert_dates(self, dict_: Dict) -> Dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, datetime):
                ret[k] = v.isoformat()
            else:
                ret[k] = v
        return ret

    def _action_for_upsert(self, index: str, objects: Iterable[DataObject], id_func: Callable,
                           field_prefix: str):
        for object_ in objects:
            obj = self._convert_data_object_to_dict(object_)
            obj = self._convert_dates(obj)
            obj = self._add_checksum(obj)
            obj = self._add_updated(obj)
            obj = self._prefix_fields(obj, field_prefix)
            uid = id_func(object_)
            obj = self._add_uid(obj, uid)
            yield {
                '_op_type': 'update',
                'doc_as_upsert': True,
                '_index': index,
                '_id': uid,
                'doc': obj
            }

    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        chunk_size: int = 100,
        id_func=lambda x: x.id,
        field_prefix: str = ''
    ) -> None:
        index = self.__get_index(object_type)
        (no_of_operations, no_of_errors) = \
            self.helpers.bulk(self.es,
                              self._action_for_upsert(index,
                                                      objects,
                                                      id_func,
                                                      field_prefix),
                              stats_only=True,
                              chunk_size=chunk_size)
        if no_of_errors > 0:
            raise DataSourceError(f'{no_of_errors} errors encountered '
                                  f'upserting {no_of_operations} objects')

    def update(
        self,
        object_type: str,
        updates: Iterable[DataObjectUpdate],
        field_prefix: str = '',
        candidate_key: Iterable[str] = []
    ) -> None:
        # This tries to find an object in the DataSource that matches
        # the candidate key. If found it will perform the update
        index = self.__get_index(object_type)
        for (_, update) in updates:
            self.es.update_by_query(
                index,
                body=self._action_for_update(index,
                                             update,
                                             field_prefix,
                                             candidate_key)

            )

    def _action_for_update(self, index: str, update: Dict,
                           field_prefix: str, candidate_key: Iterable[str]):
        u = self._convert_dates(update)
        u = self._add_checksum(u)
        u = self._add_updated(u)
        f = DataSourceFilter()
        f.exact = {}
        for key in candidate_key:
            f.exact[key] = u.pop(key)  # Don't want key in the upsert as it cannot change anyway
        u = self._prefix_fields(u, field_prefix)
        query = self._build_elasticsearch_query(
            self.__get_object_type(index),
            object_filters=f)
        return {
            'query': query,
            'script': {
                'source': "ctx._source.putAll(params['upsertWith']);",
                'lang': 'painless',
                'params': {
                    'upsertWith': u
                }
            },
        }

    def __get_index(self, object_type: str) -> str:
        return f'{self.index_prefix}-{kebabcase(object_type)}'

    def __get_object_type(self, index: str) -> str:
        start = len(self.index_prefix) + 1
        return snakecase(index[start:])

    def _field_or_keyword(self, object_type: str, name: str):
        # An attribute of the object
        if name in self.attribute_types[object_type]:
            field_type = self.attribute_types[object_type][name]
            if field_type == 'str':
                return f'{name}.keyword'
        if '.' in name:
            rc = self.relationship_config[object_type]
            relationship_name, attribute = name.split('.')[0], name.split('.')[1]
            if attribute == 'id':
                attribute = 'uid'
            relationship_object_type = rc.to_one[relationship_name]
            attribute_type = self.attribute_types[relationship_object_type][attribute]
            if attribute_type == 'str':
                return f'{name}.keyword'
        return name

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ) -> Iterable[DataObject]:
        index = self.__get_index(object_type)
        resp = self.es.mget(
            body={'ids': object_ids},
            index=index
        )
        return self._convert_dict_to_data_objects(resp['docs'])

    def get_list_page(
        self,
        object_type: str,
        page: int,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
        page_size: int = None,
        **kwargs
    ) -> Tuple[Iterable[DataObject], int]:
        index = self.__get_index(object_type)
        query = self._build_elasticsearch_query(object_type, object_filters)
        sort = self._build_elasticsearch_sort(object_type, sort_by)
        if page_size is None:
            page_size = self.get_page_size()
        from_ = (page - 1) * page_size
        resp = self.es.search(
            from_=from_,
            size=page_size,
            index=index,
            query=query,
            sort=sort
        )
        return self._convert_dict_to_data_objects(resp['hits']['hits']), \
            resp['hits']['total']['value']

    def _build_elasticsearch_query(self, object_type: str,
                                   object_filters: DataSourceFilter = None):
        if object_filters is None:
            return
        query = {'bool': {'must': [], 'must_not': []}}
        if object_filters.exact is not None:
            for k, v in object_filters.exact.items():
                if v is None:
                    query['bool']['must_not'].append({'exists': {'field': k}})
                else:
                    search_field = self._field_or_keyword(object_type, k)
                    query['bool']['must'].append({'match': {search_field: v}})

        if object_filters.contains is not None:
            for k, v in object_filters.contains.items():
                search_field = self._field_or_keyword(object_type, k)
                query['bool']['must'].append({'wildcard': {search_field:
                                                           {'value': f'{v}*', 'boost': 1.0}}})
        if object_filters.in_list is not None:
            for k, v in object_filters.in_list.items():
                search_field = self._field_or_keyword(object_type, k)
                query['bool']['must'].append({'terms': {search_field: v, 'boost': 1.0}})

        if object_filters.range is not None:
            for k, v in object_filters.range.items():
                query['bool']['must'].append({'range': {k: {'gte': v['from'],
                                                            'lte': v['to']}}})
        return query

    def _build_elasticsearch_sort(self, object_type: str, sort_by: str):
        default_sort = {'uid.keyword': 'asc'}
        if sort_by is None:
            return [default_sort]
        if sort_by.startswith('-'):
            field = self._field_or_keyword(object_type, sort_by[1:])
            order = 'desc'
        else:
            field = self._field_or_keyword(object_type, sort_by)
            order = 'asc'
        sort = [{field: order}, default_sort]
        return sort

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        index = self.__get_index(object_type)
        query = self._build_elasticsearch_query(object_type, object_filters)
        generator = self.helpers.scan(self.es,
                                      index=index,
                                      scroll='10m',
                                      size=500,
                                      query={'query': query})
        return self._convert_dict_to_data_objects(generator)

    def _convert_dict_to_data_objects(self, objs: Dict) -> Iterable:
        for obj in objs:
            type_ = self.__get_object_type(obj['_index'])
            id_ = obj['_id']
            data = obj['_source']
            yield self._convert_data_dict_to_data_object(type_, id_, data)

    def _convert_data_dict_to_data_object(self, type_, id_, data):
        attributes = {
            k: self.__make_dates(type_, k, v) for k, v in data.items()
            if k in self.attribute_types[type_].keys()
        }
        to_one_relationships = {
            k: self._convert_data_dict_to_data_object(
                self.relationship_config[type_].to_one[k],
                v['id'],
                v)
            for k, v in data.items()
            if type_ in self.relationship_config
            and self.relationship_config[type_].to_one is not None
            and k in self.relationship_config[type_].to_one.keys()
            and type(v) is dict  # i.e. not a list
        }
        return self.data_object_factory(
            type_,
            id_=id_,
            data={**attributes, **to_one_relationships}
        )

    def __make_dates(self, object_type, attribute_name, value):
        if self.attribute_types[object_type][attribute_name] == 'datetime' and \
                type(value) == str:
            return parser.parse(value)
        return value

    def get_aggregations(
            self,
            object_type: str,
            aggregations: Dict,
            object_filters: DataSourceFilter = None,
    ) -> Dict:
        index = self.__get_index(object_type)
        query = self._build_elasticsearch_query(object_type, object_filters)
        resp = self.es.search(
            size=0,
            index=index,
            query=query,
            aggregations=aggregations
        )
        return resp['aggregations']

    @property
    @cache
    def supported_types(self):
        index_names = self.es.cat.indices(h='index', s='index').split()
        return [self.__get_object_type(index_name)
                for index_name in index_names
                if index_name.startswith(self.index_prefix)]

    def __map_type(self, type_: str) -> str:
        if type_ == 'text':
            return 'str'
        if type_ == 'long':
            return 'int'
        if type_ == 'date':
            return 'datetime'
        return type_

    def _get_attribute_types_for_object_type(self, object_type: str) -> Dict:
        index_name = self.__get_index(object_type)
        mapping = self.es.indices.get_mapping(index_name)
        if 'properties' not in mapping[index_name]['mappings']:
            return {}
        properties = mapping[index_name]['mappings']['properties']
        return {
            property_name: self.__map_type(properties[property_name]['type'])
            for property_name in properties
            if 'type' in properties[property_name]
        }

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            t: self._get_attribute_types_for_object_type(t)
            for t in self.supported_types
        }

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        return self.relationship_cfg

    # This only uses the "inline" related object at the moment
    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:
        if self.relationship_config is None:
            raise DataSourceError('There are no relationships defined')
        if source.type in self.relationship_config:
            try:
                related_object_inline = getattr(source, relationship_name)
                return related_object_inline
            except AttributeError:
                return None
        return None

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Iterable[DataObject]:
        if self.relationship_config is None:
            raise DataSourceError('There are no relationships defined')
        relationship_config = self.relationship_config[source.type]
        related_object_type = relationship_config.to_many[relationship_name]
        related_object_fk_attribute = relationship_config.foreign_keys[relationship_name]

        # Get all the related objects that point to this source object
        f = DataSourceFilter()
        f.exact = {related_object_fk_attribute: source.id}
        related_objects = self.get_list(related_object_type, object_filters=f)
        return related_objects
