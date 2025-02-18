# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticSampleToElasticSequencingRequestUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        specimen = data_object.to_one_relationships['sts_specimen']
        yield (
            None,
            {
                'mlwh_sample': {'id': data_object.id},
                'mlwh_specimen.id': specimen.id
            }
        )
