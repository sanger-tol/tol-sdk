# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib.resources
from typing import Dict, Iterable, List

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection

from ..core import (
    DataObject,
    DataSource,
    DataSourceConfig,
    DataSourceError,
    DataSourceFilter
)
from ..core.operator import ListGetter


class BenchlingDataSource(DataSource, ListGetter):
    """
    A (read-only) DataSource for getting objects in Benchling
    The queries are maintained in this SDK as SQL files
    """

    def __init__(self, config: DataSourceConfig) -> None:
        super().__init__(
            config,
            [
                'username',
                'password',
                'database',
                'hostname',
                'port',
                'schema'
            ]
        )
        self.connection = self._get_connection()

    def __get_primary_keys(self):
        return {
            'sample': 'sts_id',
            'sequencing_request': 'sanger_sample_id'
        }

    def _get_connection(self) -> connection:
        return psycopg2.connect(
            user=self.username,
            password=self.password,
            database=self.database,
            port=self.port,
            host=self.hostname,
            options=f'-c search_path={self.schema},public'
        )

    def __run_query(self, sql: str) -> Iterable[DataObject]:
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            results = cur.fetchall()
            return results

    def __convert_results_to_data_objects(self, objs: Dict,
                                          object_type: str, id_col: str) -> Iterable:
        for obj in objs:
            yield self.data_object_factory(
                object_type,
                data={
                    **obj,
                    'id': obj[id_col]
                }
            )

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        file_suffix = ''
        if object_filters is not None:
            if isinstance(object_filters.exact, dict) \
                    and 'sequencing_platform' in object_filters.exact:
                file_suffix = '_sequencing_platform_' + object_filters.exact['sequencing_platform']
            else:
                raise DataSourceError('Filtering only on sequencing_platform currently supported '
                                      'on BenchlingDataSource')
        try:
            sql = importlib.resources.files('tol.benchling.sql') \
                                     .joinpath(f'{object_type}{file_suffix}.sql') \
                                     .read_text()
            results = self.__run_query(sql)
            return self.__convert_results_to_data_objects(
                results,
                object_type,
                self.__get_primary_keys()[object_type])
        except FileNotFoundError:
            raise DataSourceError(f'Query file not found for object type: {object_type} '
                                  'with given filter')

    @property
    def supported_types(self) -> List[str]:
        return self.__get_primary_keys().keys()

    def get_attribute_types(self, object_type: str) -> Dict:
        return {}
