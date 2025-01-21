# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class BoldSampleToElasticSampleUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object is not None:
            yield (None, {
                'sts_specimen.id': data_object.id
            } | data_object.attributes)
