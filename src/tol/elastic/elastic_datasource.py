# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from typing import Dict, Iterable, Tuple

from caseconverter import kebabcase

from elasticsearch import (Elasticsearch, helpers)

from ..core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)


class ElasticDataSource(DataSource):

    def __init__(self, config: Dict):
        # uri, user, password
        super().__init__(config, expected=['uri', 'user', 'password', 'index_prefix'])
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
        dhash = hashlib.md5()
        encoded = json.dumps(dict_, sort_keys=True).encode()
        dhash.update(encoded)
        return {**dict_, 'checksum': dhash.hexdigest()}

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
            yield {
                '_op_type': 'update',
                'doc_as_upsert': True,
                '_index': index,
                '_id': id_func(object_),
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

    def __get_index(self, object_type: str) -> str:
        return f'{self.index_prefix}-{kebabcase(object_type)}'

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
        **kwargs
    ) -> Tuple[Iterable[DataObject], int]:
        index = self.__get_index(object_type)
        query = self._build_elasticsearch_query(object_filters)
        page_size = self.get_page_size()
        from_ = page * page_size
        resp = self.es.search(
            from_=from_,
            size=page_size,
            index=index,
            query=query
        )
        return self._convert_dict_to_data_objects(resp['hits']['hits']), \
            resp['hits']['total']['value']

    def _build_elasticsearch_query(self, object_filters: DataSourceFilter = None):
        if object_filters is None:
            return
        query = {'bool': {'must': [], 'must_not': []}}
        if object_filters.exact is not None:
            for k, v in object_filters.exact.items():
                if v is None:
                    query['bool']['must_not'].append({'exists': {'field': k}})
                else:
                    query['bool']['must'].append({'match': {k: v}})
        if object_filters.wildcard is not None:
            for k, v in object_filters.wildcard.items():
                query['bool']['must'].append({'wildcard': {k: {'value': f'{v}*', 'boost': 1.0}}})
        if object_filters.in_list is not None:
            for k, v in object_filters.in_list.items():
                query['bool']['must'].append({'terms': {k: v, 'boost': 1.0}})
        return query

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        index = self.__get_index(object_type)
        query = self._build_elasticsearch_query(object_filters)
        generator = self.helpers.scan(self.es,
                                      index=index,
                                      query={'query': query})
        return self._convert_dict_to_data_objects(generator)

    def _convert_dict_to_data_objects(self, objs: Dict) -> Iterable:
        for obj in objs:
            yield DataObject('run-data', obj['_source'])

    def get_aggregations(
            self,
            object_type: str,
            aggregations: Dict,
            object_filters: DataSourceFilter = None,
    ) -> Dict:
        index = self.__get_index(object_type)
        query = self._build_elasticsearch_query(object_filters)
        resp = self.es.search(
            size=0,
            index=index,
            query=query,
            aggregations=aggregations
        )
        return resp['aggregations']
