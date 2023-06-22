# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List


import requests

from ..core import (
    DataObject,
    DataSourceError,
    DataSourceFilter,
    ReadOnlyDataSource,
    unsupported
)
from ..eln import (
    flatten_entity
)


class BoldDataSource(ReadOnlyDataSource):
    def __init__(self, config: Dict):
        # uri, user, password
        super().__init__(config, expected=['url'])
        self._initialise_bold()

    def _initialise_bold(self):
        pass

    def _get_specimens(self, exact_filters={}):
        url = self.url + '/index.php/API_Public/specimen'
        params = {
            **exact_filters,
            'format': 'json'
        }
        headers = {'Accept': 'application/json'}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()['bold_records']['records']
        else:
            raise DataSourceError('Error from BOLD database: ' + response.text)

    @unsupported()
    def get_by_id(self, *args, **kwargs):
        pass

    @unsupported()
    def get_list_page(self, *args, **kwargs):
        pass

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        if object_type != 'samples':
            raise DataSourceError('Only objects of type "samples" are handled by BoldDataSource')
        if object_filters is None or \
                not isinstance(object_filters.exact, dict):
            raise DataSourceError('Filter must contain an in_list filter')
        generator = self._get_specimens(object_filters.exact)
        return self._convert_dict_to_data_objects(generator)

    @unsupported()
    def get_aggregations(self, *args, **kwargs):
        pass

    def _convert_dict_to_data_objects(self, objs: Dict) -> Iterable:
        # Each "v" is a BOLD record
        for value in objs.values():
            attributes = flatten_entity(value)

            yield self.data_object_factory('sample', data=attributes)

    @property
    def supported_types(self) -> List[str]:
        raise NotImplementedError()

    def get_attribute_types(self, object_type: str) -> Dict:
        raise NotImplementedError()
