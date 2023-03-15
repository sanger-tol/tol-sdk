# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from typing import Dict, Generator, List

from cachetools import LFUCache

import irods
from irods.collection import iRODSCollection
from irods.column import Criterion, In
from irods.data_object import iRODSDataObject
from irods.models import Collection, DataObject, DataObjectMeta
from irods.session import iRODSSession

from ..core import DataSource


class IrodsDataSource(DataSource):

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
            collection_id = result[DataObject.collection_id]
            collection_object = self._get_collection(collection_id)
            data_object = iRODSDataObject(self.irods.data_objects,
                                          parent=collection_object,
                                          results=[result])
            if not re.search('(cram|bam)$', data_object.name):
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
        mapping = {'id_run': 'run_id',
                   'lane': 'position'}
        for result in results:
            new_obj = {}
            for k, v in result.items():
                if k in mapping:
                    new_obj[mapping[k]] = v
                else:
                    new_obj[k] = v
            yield new_obj

    def get_file_data(self, study_ids: List[str]):
        query = self.irods.query(DataObject) \
            .add_keyword(irods.keywords.ZONE_KW, self.query_zone)

        # Hardcode this for now
        filtered_query = query.filter(Criterion('=', DataObjectMeta.name, 'study_id')) \
            .filter(In(DataObjectMeta.value, study_ids))
        results = filtered_query.get_results()

        return self._map_keys(self._format_results(results))

    def _convert_files_to_runs(self, files: Generator):
        seen_runs = {}
        for file_ in files:
            if 'run_id' in file_ and 'position' in file_ and 'tag_index' in file_:
                key = file_['run_id'] + '_' + file_['position'] + '_' + file_['tag_index']
                if key not in seen_runs:
                    seen_runs[key] = True
                    yield {
                        'run_id': file_['run_id'],
                        'position': file_['position'],
                        'tag_index': file_['tag_index'],
                        'file_exists': True
                    }

    def get_run_data(self, study_ids: List[str]):
        files = self.get_file_data(study_ids)
        return self._convert_files_to_runs(files)
