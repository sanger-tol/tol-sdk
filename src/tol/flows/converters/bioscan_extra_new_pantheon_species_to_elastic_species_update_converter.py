# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class BioscanExtraNewPantheonSpeciesToElasticSpeciesUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object is not None and data_object.id is not None:

            yield (None, {
                'goat_scientific_name': data_object.id,
                'vernacular': data_object.vernacular,
                'conservation_status': data_object.conservation_status,
                'larval_feeding_guild': data_object.larval_feeding_guild,
                'adult_feeding_guild': data_object.adult_feeding_guild,
                'broad_biotope': data_object.broad_biotope,
                'specific_assemblage_type': data_object.specific_assemblage_type,
                'associations': data_object.associations,
                'link_to_assemblage': data_object.link_to_assemblage
            })
