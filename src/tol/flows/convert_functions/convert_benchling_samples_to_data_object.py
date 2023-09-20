# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def convert_benchling_samples_to_data_object(samples, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for s in samples:
        if s.sts_id is not None:
            yield CoreDataObject(s)
