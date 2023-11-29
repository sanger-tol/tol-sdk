# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_portaldb_sequencing_request_events_to_sequencing_requests(sres, target_datasource):
    for sre in sres:
        CoreDataObject = target_datasource.data_object_factory  # noqa N806
        ret = CoreDataObject(
            'sequencing_request',
            attributes={'sample_ref': sre.id, **sre.attributes}
        )
        yield ret
