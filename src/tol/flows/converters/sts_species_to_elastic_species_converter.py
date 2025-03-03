# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class StsSpeciesToElasticSpeciesConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        ret = self._data_object_factory(
            'species',
            data_object.id,
            attributes={
                **data_object.attributes
            }
        )

        lab_work_statuses = []
        for species_lab_work_status in data_object.species_lab_work_statuses:
            lab_work_statuses.append(
                species_lab_work_status.status
            )
        if len(lab_work_statuses) > 0:
            ret.lab_work_status = lab_work_statuses

        if data_object.sequencing_material_status is not None:
            ret.sequencing_material_status = data_object.sequencing_material_status.status
        return iter([ret])
