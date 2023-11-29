# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_specimen_status_to_data_object(status_data, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for row in status_data:
        ret = CoreDataObject('specimen', attributes={
            'tolid': row.get('sample'),
            'specimen_id': row.get('accession'),
            'status_summary': row.get('statussummary'),
            'status': row.get('status')
        })
        yield ret
