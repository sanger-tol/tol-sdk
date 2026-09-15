# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolidSpeciesToElasticSpeciesConverter(
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
        'name': 'scientific_name',
        'prefix': 'tolid_prefix',
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

        ret = self._data_object_factory(
            'species',
            data_object.id,
            attributes={
                k: v for k, v in target_attributes.items()
                if v is not None
                and str(v) != 'None'
            }
        )
        yield ret
