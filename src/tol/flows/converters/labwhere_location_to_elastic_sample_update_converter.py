# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class LabwhereLocationToElasticSampleUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object is not None:
            yield (None, {
                'sts_location': data_object.id,
                'name': data_object.name,
                'parentage': data_object.parentage
            })
