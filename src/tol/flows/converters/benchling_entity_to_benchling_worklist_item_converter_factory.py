# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    ErrorObject
)


class BenchlingEntityToBenchlingWorklistItemConverterFactory():
    def __init__(self, worklist: DataObject):
        self._worklist = worklist

    def get_converter_class(self) -> DataObjectToDataObjectOrUpdateConverter:
        factory = self

        class BenchlingEntityToBenchlingWorklistItemConverter(
                DataObjectToDataObjectOrUpdateConverter):
            def convert(self, data_object: DataObject | ErrorObject) \
                    -> Iterable[DataObject | ErrorObject]:
                if isinstance(data_object, ErrorObject):
                    yield data_object
                else:
                    ret = self._data_object_factory(
                        'worklist_item',
                        to_one={
                            'worklist': factory._worklist,
                            'item': data_object,
                        }
                    )
                    yield ret

        return BenchlingEntityToBenchlingWorklistItemConverter
