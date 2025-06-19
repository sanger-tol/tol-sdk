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
        target_to_one = {}

        if data_object.specimen is not None:
            target_to_one['tolid'] = self._data_object_factory(
                'tolid',
                data_object.specimen.id
            )

            target_to_one['specimen'] = self._data_object_factory(
                'specimen',
                data_object.specimen.supplied_name
            )
            if data_object.specimen.accession is not None:
                target_attributes['biospecimen_id'] = data_object.specimen.accession.id
            if data_object.specimen.species is not None:
                target_to_one['species'] = self._data_object_factory(
                    'species',
                    data_object.specimen.species.taxon_id
                )
        ret = self._data_object_factory(
            'sequencing_request',
            data_object.id,
            attributes=target_attributes,
            to_one=target_to_one
        )

        yield ret
