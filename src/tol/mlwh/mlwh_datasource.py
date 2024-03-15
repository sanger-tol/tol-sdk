# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import inspect
import urllib.parse
from typing import Dict, Iterable, List

import mysql.connector

from ..core import DataObject, DataSource, DataSourceError, DataSourceFilter
from ..core.operator import ListGetter


class MlwhDataSource(DataSource, ListGetter):
    def __init__(self, config: Dict):
        # uri
        super().__init__(config, expected=['uri'])
        self._initialise_mlwh()

    def _initialise_mlwh(self):
        # Connect to MLWH
        mlwh_settings = urllib.parse.urlparse(self.uri)
        self.mlwh = mysql.connector.connect(
            user=mlwh_settings.username,
            password=urllib.parse.unquote(mlwh_settings.password),
            host=mlwh_settings.hostname,
            port=mlwh_settings.port,
            database=mlwh_settings.path[1:],
        )

    def _columns_string_from_mappings(self, mappings):
        return '\n              , '.join(
            f'{col} AS {alias}' for alias, col in mappings.items()
        )

    def _get_column_mappings_iseq(self):
        return {
            'name_root': (
                # Trim file suffix, i.e. ".cram"
                'REGEXP_REPLACE(irods.irods_data_relative_path'
                ", '\\.[[:alnum:]]+$', '')"
            ),
            'study_id': 'study.id_study_lims',
            'sample_ref': 'sample.name',
            'supplier_name': 'sample.supplier_name',
            'tolid': 'sample.public_name',
            'biosample_accession': 'sample.accession_number',
            'biospecimen_accession': 'sample.donor_id',
            'scientific_name': 'sample.common_name',
            'taxon_id': 'sample.taxon_id',
            'platform_type': "'Illumina'",
            'instrument_model': 'run_lane_metrics.instrument_model',
            'instrument_name': 'run_lane_metrics.instrument_name',
            'pipeline_id_lims': 'flowcell.pipeline_id_lims',
            'run_id': 'CONVERT(product_metrics.id_run, CHAR)',
            'position': 'CONVERT(product_metrics.position, CHAR)',
            'tag_index': 'CONVERT(product_metrics.tag_index, CHAR)',
            'run_complete': 'run_lane_metrics.run_complete',
            'lims_qc': (
                'IF(product_metrics.qc IS NULL, NULL,'
                " IF(product_metrics.qc = 1, 'pass', 'fail'))"
            ),
            'qc_date': 'run_lane_metrics.qc_complete',
            'tag1_id': 'flowcell.tag_identifier',
            'tag2_id': 'flowcell.tag2_identifier',
            'library_id': 'flowcell.id_library_lims',
            'irods_path': 'irods.irods_root_collection',
            'irods_file': 'irods.irods_data_relative_path',
        }

    def _get_iseq_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_iseq()
        )

        return inspect.cleandoc(
            f"""
            SELECT {col_string}
            FROM study
            JOIN iseq_flowcell AS flowcell
              ON study.id_study_tmp = flowcell.id_study_tmp
            JOIN sample
              ON flowcell.id_sample_tmp = sample.id_sample_tmp
            JOIN iseq_product_metrics AS component_metrics
              ON flowcell.id_iseq_flowcell_tmp
                 = component_metrics.id_iseq_flowcell_tmp
            JOIN iseq_run_lane_metrics AS run_lane_metrics
              ON component_metrics.id_run = run_lane_metrics.id_run
              AND component_metrics.position = run_lane_metrics.position
            JOIN iseq_product_components AS components
              ON component_metrics.id_iseq_pr_metrics_tmp
                 = components.id_iseq_pr_component_tmp
              AND components.component_index = 1
            JOIN iseq_product_metrics AS product_metrics
              ON components.id_iseq_pr_tmp
                 = product_metrics.id_iseq_pr_metrics_tmp
            JOIN seq_product_irods_locations AS irods
              ON product_metrics.id_iseq_product = irods.id_product
            WHERE {clause}
              AND run_lane_metrics.qc_complete IS NOT NULL
              AND product_metrics.num_reads IS NOT NULL
              AND study.id_lims = 'SQSCP'
            ORDER BY run_lane_metrics.id_run
            """,
        )

    def _get_column_mappings_pacbio(self):
        return {
            'name_root': (
                'CASE WHEN run.tag2_identifier'
                ' IS NOT NULL THEN CONCAT(well_metrics.movie_name'
                ", '#', run.tag_identifier, '#', run.tag2_identifier)"
                ' WHEN run.tag_identifier IS NOT NULL'
                ' THEN CONCAT(well_metrics.movie_name'
                ", '#', run.tag_identifier)"
                ' ELSE well_metrics.movie_name END'
            ),
            'study_id': 'study.id_study_lims',
            'sample_ref': 'sample.name',
            'supplier_name': 'sample.supplier_name',
            'tolid': 'sample.public_name',
            'biosample_accession': 'sample.accession_number',
            'biospecimen_accession': 'sample.donor_id',
            'scientific_name': 'sample.common_name',
            'taxon_id': 'sample.taxon_id',
            'platform_type': "'PacBio'",
            'instrument_model': (
                "REGEXP_REPLACE(instrument_type, '^Sequel2', 'Sequel II')"
            ),
            'instrument_name': "CONCAT('m', LOWER(instrument_name))",
            'pipeline_id_lims': 'run.pipeline_id_lims',
            'run_id': 'well_metrics.movie_name',
            'lims_run_id': 'well_metrics.pac_bio_run_name',
            'well_label': 'well_metrics.well_label',
            'plate_number': 'well_metrics.plate_number',
            'run_start': 'well_metrics.run_start',
            'run_complete': 'well_metrics.run_complete',
            'lims_qc': (
                'IF(well_metrics.qc_seq IS NULL, NULL,'
                " IF(well_metrics.qc_seq = 1, 'pass', 'fail'))"
            ),
            'qc_date': 'well_metrics.qc_seq_date',
            'tag1_id': 'run.tag_identifier',
            'tag2_id': 'run.tag2_identifier',
            'library_id': 'run.pac_bio_library_tube_name',
            # Extra fields for tolqc.pacbio_run_metrics:
            'movie_minutes': 'well_metrics.movie_minutes',
            'binding_kit': 'well_metrics.binding_kit',
            'sequencing_kit': 'well_metrics.sequencing_kit',
            'include_kinetics': (
                'IF(well_metrics.include_kinetics IS NULL, NULL,'
                " IF(well_metrics.include_kinetics = 1, 'true', 'false'))"
            ),
            'loading_conc': 'well_metrics.loading_conc',
            'control_num_reads': 'well_metrics.control_num_reads',
            'control_read_length_mean': 'well_metrics.control_read_length_mean',
            'polymerase_read_bases': 'well_metrics.polymerase_read_bases',
            'polymerase_num_reads': 'well_metrics.polymerase_num_reads',
            'polymerase_read_length_mean': 'well_metrics.polymerase_read_length_mean',
            'polymerase_read_length_n50': 'well_metrics.polymerase_read_length_n50',
            'insert_length_mean': 'well_metrics.insert_length_mean',
            'insert_length_n50': 'well_metrics.insert_length_n50',
            'unique_molecular_bases': 'well_metrics.unique_molecular_bases',
            'p0_num': 'well_metrics.p0_num',
            'p1_num': 'well_metrics.p1_num',
            'p2_num': 'well_metrics.p2_num',
            'hifi_read_bases': 'well_metrics.hifi_read_bases',
            'hifi_num_reads': 'well_metrics.hifi_num_reads',
            'hifi_low_quality_num_reads': 'well_metrics.hifi_low_quality_num_reads',
            'irods_path': 'irods.irods_root_collection',
            'irods_file': 'irods.irods_data_relative_path',
        }

    def _get_pacbio_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_pacbio()
        )
        return inspect.cleandoc(
            f"""
            SELECT {col_string}
            FROM study
            JOIN pac_bio_run AS run
              ON study.id_study_tmp = run.id_study_tmp
            JOIN sample
              ON run.id_sample_tmp = sample.id_sample_tmp
            JOIN pac_bio_product_metrics AS product_metrics
              ON run.id_pac_bio_tmp = product_metrics.id_pac_bio_tmp
            JOIN pac_bio_run_well_metrics AS well_metrics
              ON product_metrics.id_pac_bio_rw_metrics_tmp
                  = well_metrics.id_pac_bio_rw_metrics_tmp
            LEFT JOIN seq_product_irods_locations AS irods
              ON product_metrics.id_pac_bio_product = irods.id_product
            WHERE {clause}
              AND well_metrics.movie_name IS NOT NULL
              AND study.id_lims = 'SQSCP'
            ORDER BY well_metrics.pac_bio_run_name
            """
        )

    def _get_column_mappings_sequencing_request(self):
        return {
            'sample_ref': 'sample.friendly_name',
            'supplier_name': 'mlwh_sample.supplier_name',
            'accession_number': 'mlwh_sample.accession_number',
            'public_name': 'mlwh_sample.public_name',
            'donor_id': 'mlwh_sample.donor_id',
            'taxon_id': 'mlwh_sample.taxon_id',
            'common_name': 'mlwh_sample.common_name',
            'description': 'mlwh_sample.description',
            'study_id': 'mlwh_study.id_study_lims',
            # 'study_uuid': 'study.uuid',
            'order_date': "DATE_FORMAT(MIN(events.created_at), '%Y-%m-%dT%H:%i:%s')",
        }

    def _get_sequencing_request_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_sequencing_request()
        )
        return inspect.cleandoc(
            f"""
            SELECT {col_string}
            FROM mlwh_events.events
            JOIN mlwh_events.event_types
              ON event_types.id = events.event_type_id
            JOIN mlwh_events.roles AS sample_roles
              ON events.id = sample_roles.event_id
              AND sample_roles.role_type_id = 6
            JOIN mlwh_events.subjects AS sample
              ON sample_roles.subject_id = sample.id
            JOIN mlwh_events.roles AS study_roles
              ON events.id = study_roles.event_id
              AND study_roles.role_type_id = 2
            JOIN mlwh_events.subjects AS study
              ON study_roles.subject_id = study.id
            LEFT JOIN mlwarehouse.sample mlwh_sample
              ON sample.friendly_name = mlwh_sample.name
              AND mlwh_sample.id_lims = 'SQSCP'
            JOIN mlwarehouse.study AS mlwh_study
              ON UNHEX(
                REPLACE(mlwh_study.uuid_study_lims, '-', '')
              ) = study.uuid
              AND mlwh_study.id_lims = 'SQSCP'
            WHERE {clause}
              AND event_types.key = 'order_made'
            GROUP BY sample.friendly_name
            """
        )

    def _get_column_mappings_long_read_qc_result(self):
        return {
            'id': 'id_long_read_qc_result_tmp',
            'labware_barcode': 'labware_barcode',
            'sample_id': 'sample_id',
            'assay_type': 'assay_type_key',
            'units': 'units',
            'value': 'value',
            'recorded_at': 'recorded_at',
            'qc_status': 'qc_status',
            'qc_status_decision_by': 'qc_status_decision_by',
        }

    def _get_long_read_qc_result_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_long_read_qc_result()
        )
        return inspect.cleandoc(
            f"""
            SELECT {col_string}
            FROM long_read_qc_result
            WHERE {clause}
            ORDER BY id_long_read_qc_result_tmp, recorded_at
            """
        )

    def _format_mlwh_row(self, object_type: str, row: Dict):
        return self.data_object_factory(
            object_type, id_=row.pop('id', None), attributes=row
        )

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
        if platform_type == 'sequencing_request':
            mappings = self._get_column_mappings_sequencing_request()
        for k, v in in_list.items():
            mapped_k = mappings[k]
            sql_conditions.append(f"{mapped_k} IN ('{self._join(v)}')")
        sql_conditions_string = ' AND '.join(sql_conditions)
        return sql_conditions_string

    def _execute_query(self, query, object_type):
        cur_mlwh = self.mlwh.cursor(dictionary=True)
        cur_mlwh.execute(query)
        for row in cur_mlwh.fetchall():
            yield self._format_mlwh_row(object_type, row)

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs,
    ) -> Iterable[DataObject]:
        # Sort out the conditions
        if object_type == 'run_data':
            if (
                object_filters is None
                or not isinstance(object_filters.exact, dict)
                or 'platform_type' not in object_filters.exact
            ):
                raise DataSourceError(
                    'Filter must contain platform_type exact filter'
                )
            if object_filters.exact['platform_type'] == 'iseq':
                sql_conditions = self._conditions_string(
                    'iseq', object_filters.in_list
                )
                query = self._get_iseq_query(sql_conditions)
                return self._execute_query(query, 'run_data')
            elif object_filters.exact['platform_type'] == 'pacbio':
                sql_conditions = self._conditions_string(
                    'pacbio', object_filters.in_list
                )
                query = self._get_pacbio_query(sql_conditions)
                return self._execute_query(query, 'run_data')
        elif object_type == 'sequencing_request':
            sql_conditions = self._conditions_string(
                'sequencing_request', object_filters.in_list
            )
            query = self._get_sequencing_request_query(sql_conditions)
            return self._execute_query(query, 'sequencing_request')
        elif object_type == 'long_read_qc_result':
            sql_conditions = self._conditions_string(
                'long_read_qc_result', object_filters.in_list
            )
            query = self._get_long_read_qc_result_query(sql_conditions)
            return self._execute_query(query, 'long_read_qc_result')
        else:
            raise DataSourceError(
                'Only objects of type long_read_qc_result, run_data or '
                'sequencing_request are supported'
            )

    @property
    def supported_types(self) -> List[str]:
        return ['long_read_qc_result', 'sequencing_request', 'run_data']
