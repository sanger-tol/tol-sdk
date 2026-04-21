# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from typing import (
    Iterable
)

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticObjectToPortaldbObjectConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        fields: dict = field(default_factory=dict)
        destination_object_type: str = 'tolid_event'
        id_field: str = 'id'
        incremental: bool = False

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config):
        super().__init__(data_object_factory)
        self.__config = config

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object is not None:

            ret = self._data_object_factory(
                self.__config.destination_object_type,
                data_object.get_field_by_name(self.__config.id_field),
                attributes=self.__config.fields
            )

            if self.__config.incremental \
                    and self.__config.destination_object_type == 'tolid_event':
                obj = ret._host.get_one(
                    'tolid_event',
                    data_object.get_field_by_name(self.__config.id_field)
                )
                count_field_value = obj.tol_tum_action_count if obj else 0
                new_count = count_field_value + 1 if count_field_value else 1
                ret.attributes['tol_tum_action_count'] = \
                    new_count if self.__config.incremental else None

            yield ret
        else:
            yield None
