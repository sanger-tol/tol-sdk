# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class StsSampleSpeciesToElasticSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        organism_parts = []
        for ssop in data_object.sample_species_organism_parts:
            organism_parts.append(ssop.organism_part.name)
        ret = self._data_object_factory(
            'sample',
            data_object.sample.id,
            attributes={
                'species': {
                    'id': str(data_object.species.id)
                },
                'lifestage':
                    data_object.lifestage.name
                    if data_object.lifestage is not None else None,
                'sex':
                    data_object.sex.name
                    if data_object.sex is not None else None,
                'organism_part': organism_parts
            }
        )
        yield ret
