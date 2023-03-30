# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from typing import Dict, Generator

from elasticsearch import (Elasticsearch, helpers)

from ..core import (
    DataSource,
    DataSourceError,
    DataSourceFilter,
    unsupported
)


class ElasticDataSource(DataSource):

    def __init__(self, config: Dict):
        # uri, user, password
        super().__init__(config, expected=['uri', 'user', 'password', 'index_prefix'])
        self._initialise_elasticsearch()

    def _initialise_elasticsearch(self):
        self.es = Elasticsearch(self.uri, http_auth=(self.user, self.password))
        self.helpers = helpers

    def _prefix_fields(self, dict_: Dict, prefix: str):
        if prefix == '':
            return dict_
        ret = {}
        for k, v in dict_.items():
            ret[prefix + '_' + k] = v
        return ret

    def _add_updated(self, dict_: Dict):
        return {**dict_, 'tol_updated_at': datetime.now()}

    def _add_checksum(self, dict_: Dict):
        dhash = hashlib.md5()
        encoded = json.dumps(dict_, sort_keys=True).encode()
        dhash.update(encoded)
        return {**dict_, 'checksum': dhash.hexdigest()}

    def _action_for_upsert(self, index: str, objects: Generator, id_func: Callable,
                           field_prefix: str):
        for object_ in objects:
            obj = self._add_checksum(object_)
            obj = self._add_updated(obj)
            obj = self._prefix_fields(obj, field_prefix)
            yield {
                '_op_type': 'update',
                'doc_as_upsert': True,
                '_index': index,
                '_id': id_func(object_),
                'doc': obj
            }

    def upsert(self, index: str, objects: Generator,
               chunk_size: int = 100,
               id_func=lambda x: x['id'],
               field_prefix: str = ''):
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

    def _action_for_update(self, index: str, objects: Generator, id_func: Callable,
                           field_prefix: str):
        for object_ in objects:
            obj = self._add_checksum(object_)
            obj = self._add_updated(obj)
            obj = self._prefix_fields(obj, field_prefix)
            yield {
                '_op_type': 'update',
                '_index': index,
                '_id': id_func(object_),
                'doc': obj
            }

    def update(self, index: str, objects: Generator,
               chunk_size: int = 100,
               id_func=lambda x: x['id'],
               field_prefix: str = ''):
        (no_of_operations, no_of_errors) = \
            self.helpers.bulk(self.es,
                              self._action_for_update(index,
                                                      objects,
                                                      id_func,
                                                      field_prefix),
                              stats_only=True,
                              chunk_size=chunk_size)
        if no_of_errors > 0:
            raise DataSourceError(f'{no_of_errors} errors encountered '
                                  f'upserting {no_of_operations} objects')

    def __get_index(self, object_type: str) -> str:
        return f'{self.index_prefix}-{object_type}'

    def get_by_id(
        self,
        object_type: str,
        id_: str,
        **kwargs
    ):
        index = self.__get_index(object_type)
        return self.es.get(
            id=id_,
            index=index
        )

    def get_list_page(
        self,
        object_type: str,
        page: int,
        object_filters: DataSourceFilter = None,
        **kwargs
    ):
        index = self.__get_index(object_type)
        page_size = self.get_page_size()
        from_ = page * page_size
        return self.es.search(
            from_=from_,
            size=page_size,
            index=index
        )

    @unsupported()
    def get_list(self, object_type: str, *args, **kwargs) -> None:
        pass
