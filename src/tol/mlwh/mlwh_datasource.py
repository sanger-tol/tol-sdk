# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import inspect
import re
import urllib.parse
from typing import Dict, Iterable, List

import mysql.connector

from ..core import DataObject, DataSource, DataSourceError, DataSourceFilter
from ..core.operator import DetailGetter, ListGetter


class MlwhDataSource(DataSource, DetailGetter, ListGetter):
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

    def _get_column_mappings_illumina(self):
        return {
            'id': (
                # Trim file suffix, i.e. ".cram"
                'REGEXP_REPLACE(irods.irods_data_relative_path'
                ", '\\.[[:alnum:]]+$', '')"
            ),
            'study_id': 'CONVERT(study.id_study_lims, SIGNED)',
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
            'element':
                'COALESCE(REGEXP_SUBSTR('
                'irods.irods_data_relative_path'
                ", '(?<=_)[^_]+(?=#)')"
                ', run_lane_metrics.position)',
            'pipeline_id_lims': 'flowcell.pipeline_id_lims',
            'run_id': 'COALESCE(REGEXP_SUBSTR('
                'irods.irods_data_relative_path, '
                "'^[^#\\.]+'"
                '), CONVERT(product_metrics.id_run, CHAR))',
            'tag_index': 'CONVERT(product_metrics.tag_index, CHAR)',
            'run_complete': 'run_lane_metrics.run_complete',
            'lims_qc': (
                'IF(product_metrics.qc IS NULL, NULL,'
                " IF(product_metrics.qc = 1, 'pass', 'fail'))"
            ),
            'cost_code': 'flowcell.cost_code',
            'qc_date': 'run_lane_metrics.qc_complete',
            'tag1_id': 'flowcell.tag_identifier',
            'tag2_id': 'flowcell.tag2_identifier',
            'library_id': 'flowcell.id_library_lims',
            'irods_path': 'irods.irods_root_collection',
            'irods_file': 'irods.irods_data_relative_path',
        }

    def _get_illumina_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_illumina()
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
              AND study.id_lims = 'SQSCP'
            ORDER BY run_lane_metrics.id_run
            """,
        )

    def _get_column_mappings_pacbio(self):
        return {
            'id': 'well_metrics.movie_name',
            'study_id': 'CONVERT(study.id_study_lims, SIGNED)',
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
            'element': 'IF(well_metrics.plate_number IS NULL'
                       ', well_metrics.well_label'
                       ', CONCAT(well_metrics.well_label'
                       ", '.'"
                       ', well_metrics.plate_number))',
            'run_start': 'well_metrics.run_start',
            'run_complete': 'well_metrics.run_complete',
            'plex_count': 'plex_agg.plex_count',
            'lims_qc': (
                'IF(well_metrics.qc_seq IS NULL, NULL,'
                " IF(well_metrics.qc_seq = 1, 'pass', 'fail'))"
            ),
            'qc_date': 'well_metrics.qc_seq_date',
            'qc_seq_state': 'well_metrics.qc_seq_state',
            'qc_seq_state_is_final': (
                'IF(well_metrics.qc_seq_state_is_final IS NULL, NULL,'
                ' IF(well_metrics.qc_seq_state_is_final = 1, true, false))'
            ),
            'cost_code': 'run.cost_code',
            'pac_bio_library_tube_name': 'run.pac_bio_library_tube_name',
            'tag1_id': 'run.tag_identifier',
            'tag2_id': 'run.tag2_identifier',
            'library_id': 'run.pac_bio_library_tube_name',
            # Extra fields for tolqc.pacbio_run_metrics:
            'movie_minutes': 'well_metrics.movie_minutes',
            'binding_kit': 'well_metrics.binding_kit',
            'sequencing_kit': 'well_metrics.sequencing_kit',
            'sequencing_kit_lot_number': 'well_metrics.sequencing_kit_lot_number',
            'cell_lot_number': 'well_metrics.cell_lot_number',
            'include_kinetics': (
                'IF(well_metrics.include_kinetics IS NULL, NULL,'
                " IF(well_metrics.include_kinetics = 1, 'true', 'false'))"
            ),
            'loading_conc': 'well_metrics.loading_conc',
            'control_num_reads': 'well_metrics.control_num_reads',
            'control_read_length_mean': 'well_metrics.control_read_length_mean',
            'control_concordance_mean': 'well_metrics.control_concordance_mean',
            'control_concordance_mode': 'well_metrics.control_concordance_mode',
            'local_base_rate': 'well_metrics.local_base_rate',
            'polymerase_read_bases': 'well_metrics.polymerase_read_bases',
            'polymerase_num_reads': 'well_metrics.polymerase_num_reads',
            'polymerase_read_length_mean': 'well_metrics.polymerase_read_length_mean',
            'polymerase_read_length_n50': 'well_metrics.polymerase_read_length_n50',
            'insert_length_mean': 'well_metrics.insert_length_mean',
            'insert_length_n50': 'well_metrics.insert_length_n50',
            'unique_molecular_bases': 'well_metrics.unique_molecular_bases',
            'productive_zmws_num': 'well_metrics.productive_zmws_num',
            'p0_num': """
                (well_metrics.p0_num * 100) /
                NULLIF((well_metrics.p0_num + well_metrics.p1_num + well_metrics.p2_num), 0)
            """,
            'p1_num': """
                (well_metrics.p1_num * 100) /
                NULLIF((well_metrics.p0_num + well_metrics.p1_num + well_metrics.p2_num), 0)
            """,
            'p2_num': """
                (well_metrics.p2_num * 100) /
                NULLIF((well_metrics.p0_num + well_metrics.p1_num + well_metrics.p2_num), 0)
            """,
            'adapter_dimer_percent': 'well_metrics.adapter_dimer_percent',
            'short_insert_percent': 'well_metrics.short_insert_percent',
            'well_hifi_read_bases': 'well_metrics.hifi_read_bases',
            'product_hifi_read_bases': 'product_metrics.hifi_read_bases',
            'hifi_num_reads': 'well_metrics.hifi_num_reads',
            'hifi_read_length_mean': 'well_metrics.hifi_read_length_mean',
            'hifi_read_quality_median': 'well_metrics.hifi_read_quality_median',
            'hifi_number_passes_mean': 'well_metrics.hifi_number_passes_mean',
            'hifi_low_quality_read_bases': 'well_metrics.hifi_low_quality_read_bases',
            'hifi_low_quality_num_reads': 'well_metrics.hifi_low_quality_num_reads',
            'hifi_low_quality_read_length_mean':
                'well_metrics.hifi_low_quality_read_length_mean',
            'hifi_low_quality_read_quality_median':
                'well_metrics.hifi_low_quality_read_quality_median',
            'hifi_barcoded_reads': 'well_metrics.hifi_barcoded_reads',
            'hifi_bases_in_barcoded_reads': 'well_metrics.hifi_bases_in_barcoded_reads',
            'irods_path': 'irods.irods_root_collection',
            'irods_file': 'irods.irods_data_relative_path',
        }

    def _get_pacbio_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_pacbio()
        )
        return inspect.cleandoc(
            f"""
            WITH plex_agg AS (
                SELECT rwm.id_pac_bio_rw_metrics_tmp, COUNT(*) plex_count
                FROM pac_bio_run_well_metrics rwm
                JOIN pac_bio_product_metrics pm
                USING (id_pac_bio_rw_metrics_tmp)
                GROUP BY rwm.id_pac_bio_rw_metrics_tmp
            )
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
            JOIN plex_agg
                ON well_metrics.id_pac_bio_rw_metrics_tmp
                = plex_agg.id_pac_bio_rw_metrics_tmp
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
            'value': 'CAST(value AS DECIMAL(20, 2))',
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

    def _get_column_mappings_study(self):
        return {
            'id': 'id_study_tmp',
            'id_lims': 'id_lims',
            'uuid_study_lims': 'uuid_study_lims',
            'id_study_lims': 'id_study_lims',
            'last_updated': 'last_updated',
            'recorded_at': 'recorded_at',
            'deleted_at': 'deleted_at',
            'created': 'created',
            'name': 'name',
            'reference_genome': 'reference_genome',
            'ethically_approved': 'ethically_approved',
            'faculty_sponsor': 'faculty_sponsor',
            'state': 'state',
            'study_type': 'study_type',
            'abstract': 'abstract',
            'abbreviation': 'abbreviation',
            'accession_number': 'accession_number',
            'description': 'description',
            'contains_human_dna': 'contains_human_dna',
            'contaminated_human_dna': 'contaminated_human_dna',
            'data_release_strategy': 'data_release_strategy',
            'data_release_sort_of_study': 'data_release_sort_of_study',
            'ena_project_id': 'ena_project_id',
            'study_title': 'study_title',
            'study_visibility': 'study_visibility',
            'ega_dac_accession_number': 'ega_dac_accession_number',
            'array_express_accession_number': 'array_express_accession_number',
            'ega_policy_accession_number': 'ega_policy_accession_number',
            'data_release_timing': 'data_release_timing',
            'data_release_delay_period': 'data_release_delay_period',
            'data_release_delay_reason': 'data_release_delay_reason',
            'aligned': 'aligned',
            'separate_y_chromosome_data': 'separate_y_chromosome_data',
            'prelim_id': 'prelim_id',
            'hmdmc_number': 'hmdmc_number',
            'data_destination': 'data_destination',
            's3_email_list': 's3_email_list',
            'data_deletion_period': 'data_deletion_period',
            'contaminated_human_data_access_group':
                'contaminated_human_data_access_group',
            'programme': 'programme',
            'ebi_library_strategy': 'ebi_library_strategy',
            'ebi_library_source': 'ebi_library_source',
            'ebi_library_selection': 'ebi_library_selection',
        }

    def _get_study_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_study()
        )
        return inspect.cleandoc(
            f"""
            SELECT {col_string}
            FROM study
            WHERE {clause}
            ORDER BY id_study_tmp
            """
        )

    def _get_column_mappings_sequencing_request_volume(self):
        return {
            'id': 'aliquot.sample_name',
            'original_volume': 'aliquot.volume',
            'insert_size': 'aliquot.insert_size',
            'concentration': 'aliquot.concentration',
            'source_barcode': 'aliquot.source_barcode',
            'volume_remaining': 'aliquot.volume - COALESCE(derived_amounts.amount, 0)'
        }

    def _get_sequencing_request_volume_query(self, clause: str):
        col_string = self._columns_string_from_mappings(
            self._get_column_mappings_sequencing_request_volume()
        )

        return inspect.cleandoc(
            f"""
            -- derived
            WITH derived_amounts AS (
                SELECT sample_name, SUM(volume) as amount
                FROM aliquot
                WHERE aliquot_type = 'derived'
                AND source_type = 'library'
                GROUP BY sample_name
            ),
            latest_primary_aliquots AS (
                SELECT sample_name, MAX(last_updated) AS latest_updated_at
                FROM aliquot
                WHERE aliquot_type = 'primary'
                AND source_type = 'library'
                GROUP BY sample_name
            )
            -- main SELECT
            SELECT {col_string}
            FROM aliquot
            LEFT JOIN derived_amounts on aliquot.sample_name = derived_amounts.sample_name
            INNER JOIN latest_primary_aliquots
                ON aliquot.sample_name = latest_primary_aliquots.sample_name
                AND aliquot.last_updated = latest_primary_aliquots.latest_updated_at
            WHERE {clause}
            AND aliquot.aliquot_type='primary'
            AND aliquot.source_type = 'library'
            """
        )

    def _get_id_from_row(self, row: Dict) -> str:
        data_id = row.get('id')
        if row.get('platform_type', '').lower() == 'pacbio':
            tag1 = self.__trimmed_tag(row.get('tag1_id'))
            tag2 = self.__trimmed_tag(row.get('tag2_id'))
            if tag2:
                return f'{data_id}#{tag1}#{tag2}'
            elif tag1:
                return f'{data_id}#{tag1}'
        return data_id

    def __trimmed_tag(self, tag):
        if tag is None:
            return tag
        if m := re.match(r'bc(\d{4,})', tag):
            return m.group(1)
        return tag

    def _format_mlwh_row(self, object_type: str, row: Dict):
        data_id = self._get_id_from_row(row)
        return self.data_object_factory(
            object_type,
            id_=data_id,
            attributes={
                k: v
                for k, v in row.items()
                if k != 'id'
            }
        )

    def _join(self, values: List) -> str:
        return "','".join([str(s) for s in values])

    def _conditions_string(self, platform_type: str, in_list: Dict):
        if in_list is None:
            return '1=1'  # Something to go with the where clause
        sql_conditions = []
        if platform_type.lower() == 'illumina':
            mappings = self._get_column_mappings_illumina()
        if platform_type.lower() == 'pacbio':
            mappings = self._get_column_mappings_pacbio()
        if platform_type.lower() == 'sequencing_request':
            mappings = self._get_column_mappings_sequencing_request()
        if platform_type.lower() == 'sequencing_request_volume':
            mappings = self._get_column_mappings_sequencing_request_volume()
        if platform_type.lower() == 'study':
            mappings = self._get_column_mappings_study()
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

    def __get_in_lists(self, f: DataSourceFilter):
        ret = {}
        for a in f.and_:
            if 'in_list' in f.and_[a] and 'value' in f.and_[a]['in_list']:
                ret[a] = f.and_[a]['in_list']['value']
        return ret

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
                or not isinstance(object_filters.and_, dict)
                or 'platform_type' not in object_filters.and_
                or 'eq' not in object_filters.and_['platform_type']
                or 'value' not in object_filters.and_['platform_type']['eq']
            ):
                raise DataSourceError(
                    'Filter must contain platform_type exact filter and list of study_ids'
                )
            if object_filters.and_['platform_type']['eq']['value'].lower() == 'illumina':
                sql_conditions = self._conditions_string(
                    'illumina', self.__get_in_lists(object_filters)
                )
                query = self._get_illumina_query(sql_conditions)
                return self._execute_query(query, 'run_data')
            elif object_filters.and_['platform_type']['eq']['value'].lower() == 'pacbio':
                sql_conditions = self._conditions_string(
                    'pacbio',
                    self.__get_in_lists(object_filters)
                )
                query = self._get_pacbio_query(sql_conditions)
                return self._execute_query(query, 'run_data')
        elif object_type == 'sequencing_request':
            sql_conditions = self._conditions_string(
                'sequencing_request',
                self.__get_in_lists(object_filters)
            )
            query = self._get_sequencing_request_query(sql_conditions)
            return self._execute_query(query, 'sequencing_request')
        elif object_type == 'long_read_qc_result':
            sql_conditions = self._conditions_string(
                'long_read_qc_result', None  # No filters
            )
            query = self._get_long_read_qc_result_query(sql_conditions)
            return self._execute_query(query, 'long_read_qc_result')
        elif object_type == 'study':
            sql_conditions = self._conditions_string(
                'study',
                self.__get_in_lists(object_filters)
            )
            query = self._get_study_query(sql_conditions)
            return self._execute_query(query, 'study')
        else:
            raise DataSourceError(
                'Only objects of type long_read_qc_result, run_data, study or '
                'sequencing_request are supported'
            )

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs,
    ) -> Iterable[DataObject]:
        # Sort out the conditions
        if object_type == 'sequencing_request_volume':
            sql_conditions = self._conditions_string(
                'sequencing_request_volume', {'id': object_ids}
            )
            query = self._get_sequencing_request_volume_query(sql_conditions)
            return self._execute_query(query, 'sequencing_request_volume')
        else:
            raise DataSourceError(
                'Only objects of type sequencing_request_volume are supported'
            )

    @property
    def supported_types(self) -> List[str]:
        return ['long_read_qc_result', 'sequencing_request', 'run_data',
                'sequencing_request_volume', 'study']
