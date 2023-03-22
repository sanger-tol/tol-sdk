# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import urllib.parse
from typing import Dict, List

import mysql.connector

from ..core import DataSource


class MlwhDataSource(DataSource):

    def __init__(self, config: Dict):
        # uri
        super().__init__(config, expected=['uri'])

        self.mlwh_connection = self._connect_to_mlwh(self.uri)

    def _connect_to_mlwh(self, uri: str):
        # Connect to MLWH
        mlwh_settings = urllib.parse.urlparse(uri)
        con_mlwh = mysql.connector.connect(user=mlwh_settings.username,
                                           password=mlwh_settings.password,
                                           host=mlwh_settings.hostname,
                                           port=mlwh_settings.port,
                                           database=mlwh_settings.path[1:])
        return con_mlwh

    def _get_iseq_query(self, clause: str):
        sql = f"""
        SELECT DISTINCT
        sample.name as sample_ref,
        sample.public_name as public_name,
        sample.common_name as common_name,
        sample.supplier_name as supplier_name,
        sample.accession_number as accession_number,
        sample.donor_id as donor_id,
        sample.taxon_id as taxon_id,
        sample.description as description,
        run_lane_metrics.instrument_model as instrument_model,
        CONVERT(run_lane_metrics.id_run, char) as run_id,
        run_lane_metrics.run_pending as start_date,
        run_lane_metrics.qc_complete as qc_date,
        CONVERT(flowcell.position, char) as position,
        CONVERT(flowcell.tag_index, char) as tag_index,
        flowcell.pipeline_id_lims as pipeline_id_lims,
        flowcell.tag_sequence as tag_sequence,
        flowcell.tag2_sequence as tag2_sequence,
        run_status_dict.description as run_status,
        run_status.date as complete_date,
        study.id_study_lims as study_id,
        study.name as study_name,
        flowcell.manual_qc as manual_qc
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

    def _get_pacbio_query(self, clause: str):
        sql = f"""
        SELECT DISTINCT
        sample.name as sample_ref,
        sample.supplier_name as supplier_name,
        sample.accession_number as accession_number,
        sample.public_name as public_name,
        sample.donor_id as donor_id,
        sample.taxon_id as taxon_id,
        sample.common_name as common_name,
        sample.description as description,
        smrtcell.pac_bio_run_name as run_id,
        smrtcell.tag_identifier as tag_index,
        smrtcell.tag_sequence as tag_sequence,
        smrtcell.well_label as position,
        smrtcell.plate_barcode as plate_barcode,
        smrtcell.pipeline_id_lims as pipeline_id_lims,
        study.id_study_lims as study_id,
        study.name as study_name,
        metrics.run_start as start_date,
        metrics.run_complete as complete_date,
        metrics.run_status as run_status,
        CONVERT(metrics.p1_num, char) as p1_num,
        metrics.movie_name as movie,
        CONVERT(metrics.hifi_read_bases, char) as yield
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

    def get_iseq_runs_by_sample_refs(self, sample_refs: List[str]):
        cur_mlwh = self.mlwh_connection.cursor(dictionary=True)
        # Only pick up runs when the QC has been done
        sample_refs_joined = "','".join(sample_refs)
        sql = self._get_iseq_query(f"sample.name IN ('{sample_refs_joined}')")
        print(sql)
        cur_mlwh.execute(sql)

        for row in cur_mlwh.fetchall():
            yield self._format_mlwh_row(row)

    def get_iseq_runs_by_study_ids(self, study_ids: List[str]):
        cur_mlwh = self.mlwh_connection.cursor(dictionary=True)
        # Only pick up runs when the QC has been done
        study_ids_joined = "','".join(study_ids)
        sql = self._get_iseq_query(f"study.id_study_lims IN ('{study_ids_joined}')")
        cur_mlwh.execute(sql)

        for row in cur_mlwh.fetchall():
            yield self._format_mlwh_row(row)

    def get_pacbio_runs_by_sample_refs(self, sample_refs: List[str]):
        cur_mlwh = self.mlwh_connection.cursor(dictionary=True)
        sample_refs_joined = "','".join(sample_refs)
        sql = self._get_pacbio_query(f"sample.name IN ('{sample_refs_joined}')")
        cur_mlwh.execute(sql)

        for row in cur_mlwh.fetchall():
            yield self._format_mlwh_row(row)

    def get_pacbio_runs_by_study_ids(self, study_ids: List[str]):
        cur_mlwh = self.mlwh_connection.cursor(dictionary=True)
        # Only pick up runs when the QC has been done
        study_ids_joined = "','".join(study_ids)
        sql = self._get_pacbio_query(f"study.id_study_lims IN ('{study_ids_joined}')")
        cur_mlwh.execute(sql)

        for row in cur_mlwh.fetchall():
            yield self._format_mlwh_row(row)

    def _format_mlwh_row(self, row: Dict):
        return row
