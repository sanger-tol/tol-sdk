# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class EnaAssemblyToElasticAssemblyConverter(
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

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object:
            attributes = {
                k: v
                for k, v in data_object.attributes.items()
                if k not in ['tax_id', 'host_tax_id']
                and v != ''
                and v != 'not provided'
            }
            to_one_relations = {
                'species': self._data_object_factory(
                    'species',
                    str(data_object.tax_id)
                )
            }
            if data_object.host_tax_id:
                to_one_relations['host_species'] = self._data_object_factory(
                    'species',
                    str(data_object.host_tax_id)
                )
            ret = self._data_object_factory(
                'assembly',
                data_object.id,
                attributes=attributes,
                to_one=to_one_relations
            )
            yield ret
