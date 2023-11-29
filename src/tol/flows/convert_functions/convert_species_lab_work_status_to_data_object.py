# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_species_lab_work_status_to_data_object(species_lab_work_statuses, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for species_lab_work_status in species_lab_work_statuses:
        attribute_name = species_lab_work_status.status.lower() + '_date'
        ret = CoreDataObject(
            'species',
            id_=species_lab_work_status.species.id,
            attributes={attribute_name: species_lab_work_status.updated_at}
        )
        yield ret
