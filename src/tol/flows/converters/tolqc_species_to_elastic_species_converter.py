# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolqcSpeciesToElasticSpeciesConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

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

        # Accessions
        if data_object.data_accession:
            target_attributes['bioproject_accession'] = data_object.data_accession.id
        if data_object.umbrella_accession:
            target_attributes['umbrella_bioproject_accession'] = data_object.umbrella_accession.id

        ret = self._data_object_factory(
            'species',
            data_object.attributes['taxon_id'],
            attributes={k: v for k, v in target_attributes.items() if v is not None}
        )
        return iter([ret])
