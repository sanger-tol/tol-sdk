# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Any, Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.data_object import ErrorObject


class BenchlingSampleCasmToStsSampleConverter(DataObjectToDataObjectOrUpdateConverter):
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
            return obj.object_.id, {
                'eln_error': {
                    'details': obj.details,
                    'object_type': obj.object_type,
                }
            }
        else:
            meta_data_object = obj.sample_metadata_id
            return meta_data_object.sts_id, {
                'eln_id': obj.id,
                'eln_updated_at': datetime.now()
            }
