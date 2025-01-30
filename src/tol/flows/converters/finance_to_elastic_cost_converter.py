# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class FinanceDatasourceToElasticCostConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        target_attributes = {
            field: str(value) if field == 'study_id' else value
            for field, value in data_object.attributes.items()
        }

        ret = self._data_object_factory(
            'cost',
            data_object.id,
            attributes=target_attributes
        )
        return iter([ret])