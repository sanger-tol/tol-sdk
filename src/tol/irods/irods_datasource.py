# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from typing import Dict, Generator, Iterable, List

from cachetools import LFUCache

import irods
from irods.collection import iRODSCollection
from irods.column import Criterion, In
from irods.data_object import iRODSDataObject
from irods.models import (
    Collection,
    DataObject as IDataObject,
    DataObjectMeta
)
from irods.session import iRODSSession

from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import ListGetter


class IrodsDataSource(DataSource, ListGetter):

    def __init__(self, config: Dict):
        # uri, user, password
        super().__init__(config, expected=['host', 'port', 'user',
                                           'password', 'zone', 'query_zone',
                                           'extra_config'])
        self._initialise_irods()
        self.cache = LFUCache(100000)

    def _initialise_irods(self):
        self.irods = iRODSSession(host=self.host,
                                  port=self.port,
                                  user=self.user,
                                  password=self.password,
                                  zone=self.zone,
                                  **self.extra_config)

    def _get_collection(self, collection_id):
        c_obj = self.cache.get(collection_id)
        if c_obj is None:
            q = self.irods.query(Collection).filter(Collection.id == collection_id) \
                .add_keyword(irods.keywords.ZONE_KW, self.query_zone)
            c_id = q.one()
            c_obj = iRODSCollection(self.irods, result=c_id)
            self.cache[collection_id] = c_obj
        return c_obj

    def _format_results(self, results: Generator):
        for result in results:
            collection_id = result[IDataObject.collection_id]
            collection_object = self._get_collection(collection_id)
            data_object = iRODSDataObject(self.irods.data_objects,
                                          parent=collection_object,
                                          results=[result])
            if not re.search('(cram|bam)$', data_object.name):
                continue
            if re.search('(scraps|removed)', data_object.name):
                continue
            metadata_keys = data_object.metadata.keys()
            metadata = {}
            for key in metadata_keys:
                metadata_objects = data_object.metadata.get_all(key)
                if len(metadata_objects) == 1:
                    metadata[key] = metadata_objects[0].value
                else:
                    metadata[key] = [x.value for x in metadata_objects]
            yield {
                'data_name': data_object.name,
                'data_id': data_object.id,
                'data_create_time': data_object.create_time,
                'collection_name': collection_object.name,
                'collection_path': collection_object.path,
                'collection_create_time': collection_object.create_time,
                **metadata
            }

    def _map_keys(self, results: Generator):
        mapping = {'id_run': 'run_id',  # Illumina
                   'run': 'run_id',  # PacBio
                   'lane': 'position',  # Illumina
                   'well': 'position',
                   'type': 'file_type'}  # PacBio
        for result in results:
            # Ignore those with target = 0
            if 'id_run' in result and 'target' in result:
                if result['target'] == '0':
                    continue
            # Ignore those with a list of tags (these are legacy)
            if 'tag_index' in result and isinstance(result['tag_index'], list):
                continue
            new_obj = {}
            for k, v in result.items():
                if k in mapping:
                    new_obj[mapping[k]] = v
                else:
                    new_obj[k] = v
            yield new_obj

    def _get_run_data(self, key_name, in_list: List[str]):
        query = self.irods.query(IDataObject) \
            .add_keyword(irods.keywords.ZONE_KW, self.query_zone)

        filtered_query = query.filter(Criterion('=', DataObjectMeta.name, key_name)) \
            .filter(In(DataObjectMeta.value, in_list))
        results = filtered_query.get_results()

        return self._map_keys(self._format_results(results))

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        if object_type != 'sequencing_file':
            raise DataSourceError('Only objects of type "sequencing_file" '
                                  'are handled by IrodsDataSource')
        if object_filters is None or \
                not isinstance(object_filters.in_list, dict):
            raise DataSourceError('Filter must contain an in_list filter')

        if 'run_id' in object_filters.in_list:
            if not isinstance(object_filters.exact, dict) or \
                    'platform_type' not in object_filters.exact:
                raise DataSourceError(
                    'Filters on run_id must also contain platform_type exact filter')
            key_names = {'iseq': 'id_run',
                         'pacbio': 'run'}
            generator = self._get_run_data(
                key_names[object_filters.exact['platform_type']],
                object_filters.in_list['run_id'])
            return self._convert_dict_to_data_objects(generator)
        elif 'study_id' in object_filters.in_list:
            generator = self._get_run_data('study_id', object_filters.in_list['study_id'])
            return self._convert_dict_to_data_objects(generator)

        raise DataSourceError('Filter must contain run_id or study_id in_list filter')

    def _convert_dict_to_data_objects(self, objs: Dict) -> Iterable[DataObject]:
        return (
            self.data_object_factory('sequencing_file', attributes=obj)
            for obj in objs
        )

    @property
    def supported_types(self):
        return ['sequencing_file']
