# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_tolqc_samples_to_data_object(samples, target_datasource):
    for sample in samples:
        CoreDataObject = target_datasource.data_object_factory  # noqa N806
        ret = CoreDataObject(
            'sample',
            attributes={
                'sample_ref': sample.name,
                'public_name': sample.specimens.name,
                'common_name': sample.specimens.species.name,
                'supplier_name': sample.specimens.supplied_name,
                'biospecimen_id': sample.specimens.accessions.name,
                'taxon_id': sample.specimens.species.taxon_id
            }
        )
        yield ret
