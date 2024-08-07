# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class MlwhRunDataToElasticRunDataConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:

        attributes = {
            k: v
            for k, v in data_object.attributes.items()
            if k not in ['supplier_name', 'taxon_id', 'sample_ref', 'tolid']
        }
        to_one_relations = {
            'specimen': self._data_object_factory(
                'specimen',
                data_object.supplier_name),
            'species': self._data_object_factory(
                'species',
                str(data_object.taxon_id)
            ),
            'sequencing_request': self._data_object_factory(
                'sequencing_request',
                data_object.sample_ref
            ),
            'tolid': self._data_object_factory(
                'tolid',
                data_object.tolid
            )
        }
        ret = self._data_object_factory(
            'run_data',
            data_object.id,
            attributes=attributes,
            to_one=to_one_relations
        )
        yield ret
