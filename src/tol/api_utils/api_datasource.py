# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import math
from itertools import chain
from typing import Dict, List

from cachetools import LFUCache

import requests

from .api_object import ApiObject
from ..core import (
    DataSource,
    DataSourceError
)


class ApiDataSource(DataSource):

    def __init__(self, config):
        """Initialises an API base data source.

        We expect the following keys in the config:
        url -- the URL of the instance (including path with API prefix)
        key -- the API key to use for authentication
        """
        super(ApiDataSource, self).__init__(config)
        self.cache = LFUCache(100000)  # Might want to make this configurable at some point

    def get_by_id(self, object_type: str, id_: int):
        url = f'{object_type}/{id_}'
        ret, _ = self.get_by_link(url)
        return ret

    def get_by_link(self, link: str, params: Dict = {}):
        response = requests.get(f'{self.url}/{link}', params=params)
        if response.status_code != 200:
            raise DataSourceError('Cannot find object(s)',
                                  response.text,
                                  response.status_code)
        json = response.json()
        meta = json['meta'] if 'meta' in json else {'total': 1}
        return self.unpack(json), meta

    def get_list(self, object_type: str, filter_: str = '',
                 sort_by: str = '', page_size: int = 100):
        # Get the first page, then we know the total size
        args = {'filter': filter_,
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
            cached_object.update_attributes_from_json(obj_dict['attributes'])
            return cached_object
        new_object = ApiObject.create(obj_dict)
        self.cache[key] = new_object
        return new_object

    def delete_by_id(self, object_type: str, id_: int):
        url = f'{object_type}/{id_}'
        response = requests.delete(f'{self.url}/{url}')
        if response.status_code != 204:
            raise DataSourceError('Cannot find object(s)',
                                  response.text,
                                  response.status_code)
        return

    def create(self, obj: ApiObject):
        url = f'{obj.type}'
        json = {'data': obj.to_json()}
        response = requests.post(f'{self.url}/{url}', json=json)
        if response.status_code != 200:
            raise DataSourceError('Cannot create object',
                                  response.text,
                                  response.status_code)
        json = response.json()
        obj._id = json['data']['id']
        obj.update_attributes_from_json(json['data']['attributes'])
        return obj

    def update(self, obj: ApiObject):
        url = f'{obj.type}/{obj.id}'
        json = {'data': obj.to_json()}
        response = requests.patch(f'{self.url}/{url}', json=json)
        if response.status_code != 200:
            raise DataSourceError('Cannot update object',
                                  response.text,
                                  response.status_code)
        json = response.json()
        obj.update_attributes_from_json(json['data']['attributes'])
        return obj
