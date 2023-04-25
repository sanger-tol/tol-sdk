# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import math
from itertools import chain
from typing import Dict, List

from cachetools import LFUCache

import requests

from .old_api_object import OldApiObject
from ..core import (
    DataSource,
    DataSourceError,
    DataSourceFilter,
    unsupported
)


class OldApiDataSource(DataSource):

    def __init__(self, config: Dict):
        """Initialises an API base data source.

        We expect the following keys in the config:
        url -- the URL of the instance (including path with API prefix)
        key -- the API key to use for authentication
        """
        super().__init__(config, expected=['url', 'key'])
        self.cache = LFUCache(100000)  # Might want to make this configurable at some point

    def get_by_id(self, object_type: str, id_: int):
        url = f'{object_type}/{id_}'
        ret, _ = self.get_by_link(url)
        return ret

    def _get(self, path, params):
        return requests.get(f'{self.url}{path}', params=params)

    def _post(self, path, json):
        return requests.post(f'{self.url}/{path}', json=json,
                             headers={'Token': self.key})

    def _patch(self, path, json):
        return requests.patch(f'{self.url}/{path}', json=json,
                              headers={'Token': self.key})

    def _delete(self, path):
        return requests.delete(f'{self.url}/{path}')

    def get_by_link(self, link: str, params: Dict = {}):
        response = self._get(f'/{link}', params=params)
        if response.status_code != 200:
            raise DataSourceError('Cannot find object(s)',
                                  response.text,
                                  response.status_code)
        json = response.json() if callable(response.json) else response.json
        meta = json['meta'] if 'meta' in json else {'total': 1}
        return self.unpack(json), meta

    def get_list(self, object_type: str, object_filters: DataSourceFilter = None,
                 sort_by: str = '', page_size: int = 100):
        # Get the first page, then we know the total size
        args = {'filter': json.dumps(object_filters) if object_filters else {},
                'sort_by': sort_by,
                'page_size': page_size}
        first_page, meta = self.get_list_page(object_type, 1, **args)
        total_rows = meta['total']
        last_page = math.ceil(total_rows / page_size)
        if last_page == 1:
            return first_page

        pages = range(2, last_page + 1)
        return chain(first_page,
                     self.get_list_pages(object_type, pages, **args))

    def get_list_pages(self, object_type: str, pages: List, **kwargs):
        for page in pages:
            page, _ = self.get_list_page(object_type, page, **kwargs)
            yield from page

    def get_list_page(self, object_type: str, page: int, **kwargs):
        url = f'{object_type}'
        return self.get_by_link(url, params={**kwargs, 'page': page})

    def unpack(self, json):
        if type(json['data']) is list:
            ret = []
            for obj in json['data']:
                ret.append(self.new_or_from_cache(obj))
            return ret

        # Single object
        return self.new_or_from_cache(json['data'])

    def new_or_from_cache(self, obj_dict: Dict):
        id_ = obj_dict['id']
        type_ = obj_dict['type']
        key = f'{type_}{id_}'
        if key in self.cache:
            cached_object = self.cache[key]
            cached_object.update_attributes_from_dict(obj_dict['attributes'])
            return cached_object
        new_object = OldApiObject(type_, id_)
        self._update_object_from_json(new_object, obj_dict)
        self._cache_object(new_object)
        return new_object

    def _cache_object(self, obj):
        id_ = obj.id
        type_ = obj.type
        key = f'{type_}{id_}'
        self.cache[key] = obj

    def _convert_relationships_from_json_to_objects(self, relationships: Dict):
        # We see both one- and many- ends of the relationships here
        ret = {}
        for k, v in relationships.items():
            if 'data' in v and v['data'] is not None:  # Relationship to single object
                ret[k] = self._get_from_cache_or_remote(v['data']['type'], v['data']['id'])
            # Ignore many end
        return ret

    def _update_attributes_from_object(self, obj: OldApiObject):
        for k in obj.attributes.keys():
            obj.attributes[k] = getattr(obj, k)

    def _update_relationships_from_object(self, obj: OldApiObject):
        for k in obj.relationships.keys():
            obj.relationships[k] = getattr(obj, k)

    def _get_from_cache_or_remote(self, type_, id_):
        key = f'{type_}{id_}'
        if key in self.cache:
            return self.cache.get(key)
        return self.get_by_id(type_, id_)

    def delete_by_id(self, object_type: str, id_: int):
        url = f'/{object_type}/{id_}'
        response = self._delete(url)
        if response.status_code != 204:
            raise DataSourceError('Cannot find object(s)',
                                  response.text,
                                  response.status_code)
        return

    def delete(self, obj: OldApiObject):
        return self.delete_by_id(obj.type, obj.id)

    def _update_object_from_json(self, obj: OldApiObject, obj_json: Dict):
        obj._id = obj_json['id']
        obj.update_attributes_from_dict(obj_json.get('attributes', {}))
        if 'relationships' in obj_json:
            relationships_obj = \
                self._convert_relationships_from_json_to_objects(obj_json['relationships'])
            obj.update_relationships_from_dict(relationships_obj)

    @unsupported
    def upsert(self, object_type: str, *args, **kwargs) -> None:
        pass

    @unsupported
    def upsert_multiple_type(self, *args, **kwargs) -> None:
        pass
