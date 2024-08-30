# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class BioscanExtraSpeciesToElasticSpeciesUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object is not None:
            yield (None, {
                'goat_scientific_name': data_object.id,
                'goat_phylum_name': 'Arthropoda',
                **data_object.attributes
            })
