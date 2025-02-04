# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    ErrorObject
)
from ...core.operator.updater import DataObjectUpdate


class LabwhereLocationToElasticSampleUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object is not None:
            # Validate all mandatory fields
            mandatory_fields = {
                'id': data_object.id,
                'name': data_object.name,
                'parentage': data_object.parentage
            }

            if not all(mandatory_fields.values()):
                missing = [k for k, v in mandatory_fields.items() if not v]
                error = ErrorObject(
                    details={'message': f"Missing mandatory fields: {', '.join(missing)}"},
                    object_type='location',
                    object_id=data_object.id,
                    object_=data_object,
                    http_code=400
                )
                yield error
                return

        yield (None, {
            'sts_location': data_object.id,
            'name': data_object.name,
            'parentage': data_object.parentage
        })
