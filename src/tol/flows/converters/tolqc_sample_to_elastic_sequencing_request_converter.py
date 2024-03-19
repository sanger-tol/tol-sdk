# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TolqcSampleToElasticSequencingRequestConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        target_attributes = {**data_object.attributes}

        if data_object.specimen is not None:
            target_attributes['tolid'] = {'id': data_object.specimen.id}
            target_attributes['specimen'] = {'id': data_object.specimen.supplied_name}
            if data_object.specimen.accession is not None:
                target_attributes['biospecimen_id'] = data_object.specimen.accession.id
            if data_object.specimen.species is not None:
                target_attributes['species'] = {'id': data_object.specimen.species.id}

        ret = self._data_object_factory(
            'sequencing_request',
            data_object.id,
            attributes=target_attributes
        )

        return iter([ret])
