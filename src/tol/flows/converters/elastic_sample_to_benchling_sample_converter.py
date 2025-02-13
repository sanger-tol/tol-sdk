# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSampleToBenchlingSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if 'benchling_eln_tissue_id' in data_object.attributes:
            # Extract the relationships first
            species = data_object.to_one_relationships.get('benchling_species')
            specimen = data_object.to_one_relationships.get('benchling_specimen')
            tolid = data_object.to_one_relationships.get('benchling_tolid')

            # Create attributes dict removing benchling_ prefix
            attributes = {
                k[10:]: v  # Remove 'benchling_' prefix
                for k, v in data_object.attributes.items()
                # eln_tissue_id is a unique marker and should be treated separately
                if k.startswith('benchling_') and k != 'benchling_eln_tissue_id'
            }

            # Add the relationship IDs to attributes
            if species:
                attributes['taxon_id'] = species.id
            if specimen:
                attributes['specimen_id'] = specimen.id
            if tolid:
                attributes['programme_id'] = tolid.id

            attributes['sts_id'] = data_object.id

            ret = self._data_object_factory(
                'sample',
                data_object.attributes['benchling_eln_tissue_id'],
                attributes=attributes
            )
            yield ret
