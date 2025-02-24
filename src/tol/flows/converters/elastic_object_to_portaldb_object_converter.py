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
                 destination_object_type: str = 'tolid_event'):
        super().__init__(data_object_factory)
        self.__fields = fields
        self.__destination_object_type = destination_object_type

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object is not None:
            ret = self._data_object_factory(
                self.__destination_object_type,
                data_object.id,
                attributes=self.__fields
            )
            yield ret
        else:
            yield None
