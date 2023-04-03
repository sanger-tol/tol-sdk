# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import urllib.parse
from typing import Dict, Iterable, List

import mysql.connector

from ..core import (
    DataObject,
    DataSourceError,
    DataSourceFilter,
    ReadOnlyDataSource,
    unsupported
)


class MlwhDataSource(ReadOnlyDataSource):

    def __init__(self, config: Dict):
        # uri
        super().__init__(config, expected=['uri'])
        self._initialise_mlwh()

    def _initialise_mlwh(self):
        # Connect to MLWH
        mlwh_settings = urllib.parse.urlparse(self.uri)
        self.mlwh = mysql.connector.connect(user=mlwh_settings.username,
                                            password=mlwh_settings.password,
                                            host=mlwh_settings.hostname,
                                            port=mlwh_settings.port,
                                            database=mlwh_settings.path[1:])

    def _get_column_mappings_iseq(self):
        return {
            'sample_ref': 'sample.name',
            'public_name': 'sample.public_name',
            'common_name': 'common_name',
            'supplier_name': 'sample.supplier_name',
            'accession_number': 'sample.accession_number',
            'donor_id': 'sample.donor_id',
            'taxon_id': 'sample.taxon_id',
            'description': 'sample.description',
            'instrument_model': 'run_lane_metrics.instrument_model',
            'run_id': 'CONVERT(run_lane_metrics.id_run, char)',
            'start_date': 'run_lane_metrics.run_pending',
            'qc_date': 'run_lane_metrics.qc_complete',
            'position': 'CONVERT(flowcell.position, char)',
            'tag_index': 'CONVERT(flowcell.tag_index, char)',
            'pipeline_id_lims': 'flowcell.pipeline_id_lims',
            'tag_sequence': 'flowcell.tag_sequence',
            'tag2_sequence': 'flowcell.tag2_sequence',
            'run_status': 'run_status_dict.description',
            'complete_date': 'run_status.date',
            'study_id': 'study.id_study_lims',
            'study_name': 'study.name',
            'manual_qc': 'flowcell.manual_qc'
        }

    def _get_iseq_query(self, clause: str):
        mappings = self._get_column_mappings_iseq()
        col_string = ','.join([f'{v} as {k}' for k, v in mappings.items()])
        sql = f"""
        SELECT DISTINCT
        {col_string},
        'iseq' as platform_type
        FROM mlwarehouse.sample
        JOIN (mlwarehouse.iseq_flowcell as flowcell,
        mlwarehouse.iseq_run_status as run_status,
        mlwarehouse.iseq_product_metrics as product_metrics,
        mlwarehouse.iseq_run_lane_metrics as run_lane_metrics,
        iseq_run_status_dict as run_status_dict,
        mlwarehouse.study as study)
        ON (flowcell.id_sample_tmp = sample.id_sample_tmp
        AND product_metrics.id_iseq_flowcell_tmp = flowcell.id_iseq_flowcell_tmp
        AND run_status.id_run = product_metrics.id_run
        AND run_status.id_run = run_lane_metrics.id_run
        AND run_status.id_run_status_dict = run_status_dict.id_run_status_dict
        AND flowcell.id_study_tmp = study.id_study_tmp)
        WHERE {clause}
        AND run_status.iscurrent = 1
        AND qc_complete is not null
        ORDER BY run_lane_metrics.id_run;
        """
        return sql

    def _get_column_mappings_pacbio(self):
        return {
            'sample_ref': 'sample.name',
            'supplier_name': 'sample.supplier_name',
            'accession_name': 'sample.accession_number',
            'public_name': 'sample.public_name',
            'donor_id': 'sample.donor_id',
            'taxon_id': 'sample.taxon_id',
            'common_name': 'sample.common_name',
            'description': 'sample.description',
            'run_id': 'smrtcell.pac_bio_run_name',
            'tag_index': 'smrtcell.tag_identifier',
            'tag_sequence': 'smrtcell.tag_sequence',
            'position': 'smrtcell.well_label',
            'plate_barcode': 'smrtcell.plate_barcode',
            'pipeline_id_lims': 'smrtcell.pipeline_id_lims',
            'study_id': 'study.id_study_lims',
            'study_name': 'study.name',
            'start_date': 'metrics.run_start',
            'complete_date': 'metrics.run_complete',
            'run_status': 'metrics.run_status',
            'p1_num': 'CONVERT(metrics.p1_num, char)',
            'movie': 'metrics.movie_name',
            'yield': 'CONVERT(metrics.hifi_read_bases, char)'
        }

    def _get_pacbio_query(self, clause: str):
        mappings = self._get_column_mappings_pacbio()
        col_string = ','.join([f'{v} as {k}' for k, v in mappings.items()])
        sql = f"""
        SELECT DISTINCT
        {col_string},
        'pacbio' as platform_type
        FROM mlwarehouse.sample
        JOIN (mlwarehouse.pac_bio_run as smrtcell,
        mlwarehouse.pac_bio_run_well_metrics as metrics,
        mlwarehouse.study as study)
        ON (smrtcell.id_sample_tmp = sample.id_sample_tmp
        AND smrtcell.id_pac_bio_run_lims = metrics.pac_bio_run_name
        AND smrtcell.well_label = metrics.well_label
        AND smrtcell.id_study_tmp = study.id_study_tmp)
        WHERE {clause}
        AND metrics.run_complete is not null
        ORDER BY smrtcell.pac_bio_run_name
        """
        return sql

    def _format_mlwh_row(self, object_type: str, row: Dict):
        return DataObject(object_type, row)

    def _join(self, values: List) -> str:
        return "','".join(values)

    def _conditions_string(self, platform_type: str, in_list: Dict):
        if in_list is None:
            return '1=1'  # Something to go with the where clause
        sql_conditions = []
        if platform_type == 'iseq':
            mappings = self._get_column_mappings_iseq()
        if platform_type == 'pacbio':
            mappings = self._get_column_mappings_pacbio()
        for k, v in in_list.items():
            mapped_k = mappings[k]
            sql_conditions.append(f"{mapped_k} IN ('{self._join(v)}')")
        sql_conditions_string = ' AND '.join(sql_conditions)
        return sql_conditions_string

    def _execute_query(self, query):
        cur_mlwh = self.mlwh.cursor(dictionary=True)
        cur_mlwh.execute(query)
        for row in cur_mlwh.fetchall():
            yield self._format_mlwh_row('run_data', row)

    @unsupported()
    def get_by_id(self, *args, **kwargs):
        pass

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        # Sort out the conditions
        if object_type != 'run_data':
            raise DataSourceError('Only objects of type run_data are supported')
        if object_filters is None or \
                not isinstance(object_filters.exact, dict) or \
                'platform_type' not in object_filters.exact:
            raise DataSourceError('Filter must contain platform_type exact filter')
        if object_filters.exact['platform_type'] == 'iseq':
            sql_conditions = self._conditions_string('iseq', object_filters.in_list)
            query = self._get_iseq_query(sql_conditions)
            return self._execute_query(query)
        elif object_filters.exact['platform_type'] == 'pacbio':
            sql_conditions = self._conditions_string('pacbio', object_filters.in_list)
            query = self._get_pacbio_query(sql_conditions)
            return self._execute_query(query)

    @unsupported()
    def get_list_page(self, *args, **kwargs):
        pass
