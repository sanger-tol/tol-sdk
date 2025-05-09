# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class MlwhSequencingRequestToElasticSequencingRequestConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        attributes = {
            k: v
            for k, v in data_object.attributes.items()
            if k not in ['taxon_id', 'public_name', 'sample_ref', 'supplier_name']
        }
        to_one_relations = {
            'specimen': self._data_object_factory(
                'specimen',
                data_object.supplier_name),
            'species': self._data_object_factory(
                'species',
                str(data_object.taxon_id)
            ),
            'tolid': self._data_object_factory(
                'tolid',
                data_object.public_name
            )
        }
        ret = self._data_object_factory(
            'sequencing_request',
            data_object.sample_ref,
            attributes=attributes,
            to_one=to_one_relations
        )
        yield ret
