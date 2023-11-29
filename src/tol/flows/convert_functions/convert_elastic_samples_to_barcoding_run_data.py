# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_elastic_samples_to_barcoding_run_data(samples, target_datasource):
    for sample in samples:
        CoreDataObject = target_datasource.data_object_factory  # noqa N806
        ret = CoreDataObject(
            'barcoding_run_data',
            attributes={
                'col_date': sample.col_date,
                'taxon_id': sample.id
            }
        )
        yield ret
