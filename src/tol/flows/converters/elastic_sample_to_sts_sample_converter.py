# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSampleToStsSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object.tolid_tolid is not None:
            yield self._data_object_factory(
                'sample',
                data_object.id,
                attributes={
                    'public_name': data_object.tolid_tolid.id,
                }
            )
