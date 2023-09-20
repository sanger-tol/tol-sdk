# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

def convert_bioscan_barcoding_run_data_to_data_object(brds, target_datasource):
    CoreDataObject = target_datasource.data_object_factory  # noqa N806
    for b in brds:
        ret = CoreDataObject('barcoding_run_data', b)
        yield ret
