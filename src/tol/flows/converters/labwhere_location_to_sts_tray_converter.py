# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class LabwhereLocationToStsTrayConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object is not None:
            yield self._data_object_factory(
                'freezer_tray',
                data_object.id,
                attributes={
                    'name': data_object.name,
                    'parentage': data_object.parentage
                }
            )
