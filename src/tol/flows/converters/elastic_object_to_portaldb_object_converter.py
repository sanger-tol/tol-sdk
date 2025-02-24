# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import (
    Iterable
)

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticObjectToPortaldbObjectConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def __init__(self, data_object_factory, fields: dict = {},
                 destination_object_type: str = 'tolid_event',
                 id_field: str = 'id'):
        super().__init__(data_object_factory)
        self.__fields = fields
        self.__destination_object_type = destination_object_type
        self.__id_field = id_field

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object is not None:
            ret = self._data_object_factory(
                self.__destination_object_type,
                data_object.get_field_by_name(self.__id_field),
                attributes=self.__fields
            )
            yield ret
        else:
            yield None
