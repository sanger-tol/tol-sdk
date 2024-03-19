# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolqcSpeciesToElasticSpeciesConverter(
        DataObjectToDataObjectOrUpdateConverter):

    ATTRIBUTE_MAPPING = {
        'taxon_family': 'family',
        'taxon_group': 'group',  # change if necessary
        'taxon_order': 'order_group',
        'taxon_phylum': 'taxon_group',
    }

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        target_attributes = {}

        for source_attr, source_value in data_object.attributes.items():
            # if attribute is mapped, use the mapped attribute name
            if source_attr in self.ATTRIBUTE_MAPPING:
                target_attr = self.ATTRIBUTE_MAPPING[source_attr]
            # else, use attribute name as is
            else:
                target_attr = source_attr

            # add attribute to the target dictionary
            target_attributes[target_attr] = source_value

        target_attributes['scientific_name'] = data_object.id
        target_attributes.pop('taxon_id', None)

        ret = self._data_object_factory(
            'species',
            data_object.attributes['taxon_id'],
            attributes=target_attributes
        )
        return iter([ret])
