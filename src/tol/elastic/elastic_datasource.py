# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from typing import Dict, Generator

from elasticsearch import (Elasticsearch, helpers)

from ..core import (DataSource, DataSourceError)


class ElasticDataSource(DataSource):

    def __init__(self, config: Dict):
        # uri, user, password
        super().__init__(config, expected=['uri', 'user', 'password'])
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

    def _action_for_upsert(self, index: str, objects: Generator, id_func: Callable,
                           field_prefix: str):
        for object_ in objects:
            yield {
                '_op_type': 'update',
                'doc_as_upsert': True,
                '_index': index,
                '_id': id_func(object_),
                'doc': self._prefix_fields(object_, field_prefix)
            }

    def upsert(self, index: str, objects: Generator,
               data_filter=None,
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
            yield {
                '_op_type': 'update',
                '_index': index,
                '_id': id_func(object_),
                'doc': self._prefix_fields(object_, field_prefix)
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

    def get_list_page(
        self,
        object_type: str,
        page: int,
        data_filter=None,
        **kwargs
    ):
        raise NotImplementedError()

    def get_by_id(
        self,
        object_type: str,
        id: str,
        **kwargs
    ):
        pass
