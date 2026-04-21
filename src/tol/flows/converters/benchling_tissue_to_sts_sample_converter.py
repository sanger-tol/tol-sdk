# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.data_object import ErrorObject


class BenchlingTissueToStsSampleConverter(
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
        id_, attributes_ = self.__get_sample_upsert_id_and_attributes(data_object)
        ret = self._data_object_factory(
            'sample',
            str(id_),
            attributes=attributes_
        )
        yield ret

    def __get_sample_upsert_id_and_attributes(
        self,
        obj: DataObject | ErrorObject
    ) -> [str, dict[str, Any]]:

        if isinstance(obj, ErrorObject):
            return obj.object_.sts_id, {
                'eln_error': {
                    'details': obj.details,
                    'object_type': obj.object_type,
                }
            }
        else:
            return obj.sts_id, {
                'eln_id': obj.id,
                'eln_updated_at': datetime.now(),
                'ep_exported': True
            }
