# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class BioscanQcSpecimenToElasticSampleUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object is not None and data_object.id is not None:

            yield (None, {
                'sts_specimen.id': data_object.id,
                'sanger_qc_result': data_object.sanger_qc_result,
                'sanger_qc_description': data_object.sanger_qc_description})
