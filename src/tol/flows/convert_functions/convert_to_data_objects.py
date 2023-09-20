# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_to_data_objects(runs, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for run in runs:
        yield CoreDataObject('sequencing_file', run)
