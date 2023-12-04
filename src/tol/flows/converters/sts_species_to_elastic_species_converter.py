# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectConverter
)


class StsSpeciesToElasticSpeciesConverter(
        DataObjectToDataObjectConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        ret = self._data_object_factory(
            'species',
            data_object.id,
            attributes={
                **data_object.attributes
            }
        )
        if data_object.sequencing_material_status is not None:
            ret.sequencing_material_status = data_object.sequencing_material_status.status
        return iter([ret])
