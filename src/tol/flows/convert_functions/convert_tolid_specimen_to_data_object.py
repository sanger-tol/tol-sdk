# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_tolid_specimen_to_data_object(specimens, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for s in specimens:
        ret = CoreDataObject('specimen', {
            'specimen_id': s.specimen_id,
            'tolid': s.tolid,
            'taxon_id': s.species.id
        })
        yield ret
