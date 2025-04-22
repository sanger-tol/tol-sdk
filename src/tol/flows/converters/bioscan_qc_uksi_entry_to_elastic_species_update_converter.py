# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class BioscanQcUksiEntryToElasticSpeciesUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object is not None and data_object.id is not None:

            yield (None, {
                'goat_scientific_name': data_object.id,
                'uksi_name_status': data_object.uksi_name_status})
