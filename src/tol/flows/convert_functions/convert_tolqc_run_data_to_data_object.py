# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_tolqc_run_data_to_data_object(run_data, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for run_datum in run_data:
        ret = CoreDataObject(
            'run_data',
            attributes={'run_id': run_datum.runs.name,
                        'position': run_datum.runs.element,
                        'tag_index': run_datum.tag_index,
                        'sample_ref': run_datum.samples.name,
                        'public_name': run_datum.samples.specimens.name,
                        'common_name': run_datum.samples.specimens.species.name,
                        'supplier_name': run_datum.samples.specimens.supplied_name,
                        'biospecimen_id': run_datum.samples.specimens.accessions.name,
                        'taxon_id': run_datum.samples.specimens.species.taxon_id,
                        'instrument_model': run_datum.runs.platforms.model,
                        'start_date': run_datum.runs.start_date,
                        'qc_date': run_datum.runs.qc_date,
                        'pipeline_id_lims': '',  # TODO
                        'tag_sequence': run_datum.tag1_id,
                        'tag2_sequence': run_datum.tag2_id,
                        'complete_date': run_datum.runs.date,
                        'manual_qc': run_datum.lims_qc}
        )
        yield ret
