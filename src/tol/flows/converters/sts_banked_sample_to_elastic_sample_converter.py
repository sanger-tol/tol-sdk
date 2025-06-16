# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class StsBankedSampleToElasticSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        ret = self._data_object_factory(
            'sample',
            data_object.id,
            attributes={
                **data_object.attributes
            }
        )
        if data_object.category is not None:
            ret.banked_sample_category = data_object.category.name
        yield ret
