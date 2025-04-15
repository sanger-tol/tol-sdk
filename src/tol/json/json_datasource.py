# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import cache
from typing import Any, Dict, Iterable, Optional

from dateutil import parser as dateutil_parser

import requests

from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import (
    DetailGetter,
    ListGetter
)


class JsonDataSource(
    DataSource,

    # the supported operators
    DetailGetter,
    ListGetter
):
    """
    A `DataSource` that connects to a remote JSON data file
    """

    def __init__(
        self,
        config: Dict
    ) -> None:
        super().__init__(
            config,
            expected=['uri', 'type', 'id_attribute', 'mappings']
        )
        self._raw_data = self._load_json()
        self._keyed_by_id = {
            v[self.id_attribute]: v
            for v in self._raw_data
            if self.id_attribute in v
        }

    def _load_json(self):
        response = requests.get(self.uri)
        if response.status_code != 200:
            raise DataSourceError()
        data = response.json()
        return data

    def __map_entry(self, entry: Dict):
        ret = {}
        for mapping_key, mapping_value in self.mappings.items():
            if mapping_value['heading'] != self.id_attribute:
                subentry = entry
                for level in mapping_value['heading'].split('.'):
                    if subentry is not None:
                        subentry = subentry.get(level)
                ret[mapping_key] = self.__parse_date(mapping_key, subentry)
        return ret

    def __create_data_object(self, entry: Dict):
        return self.data_object_factory(
            self.type,
            entry.get(self.id_attribute),
            attributes=self.__map_entry(entry)
        )

    def __parse_date(self, attribute_name: str, value: Any):
        if self.mappings[attribute_name]['type'] == 'datetime' and value is not None:
            return dateutil_parser.parse(value)
        if self.mappings[attribute_name]['type'] == 'str' and value is not None:
            return str(value)
        return value

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            self.type: {
                k: v['type']
                for k, v in self.mappings.items()
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs,
    ) -> Iterable[Optional[DataObject]]:
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')

        return (
            self.__create_data_object(self._keyed_by_id[object_id])
            if self._keyed_by_id[object_id] is not None else None
            for object_id in object_ids
        )

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None
    ) -> Iterable[DataObject]:
        """
        Gets an Iterable of DataObject instances of the given
        type, according to the given DataSourceFilter.
        """
        if object_filters is not None:
            raise DataSourceError('Filtering is not supported on JsonDataSource')
        if object_type not in self.supported_types:
            raise DataSourceError(f'{object_type} is not supported')
        for entry in self._raw_data:
            id_ = entry.get(self.id_attribute)
            if id_ is not None and id_ != '':
                yield self.__create_data_object(entry)
