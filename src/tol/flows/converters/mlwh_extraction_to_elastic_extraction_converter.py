# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class MlwhExtractionToElasticExtractionConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        prefix = data_object.assay_type.lower()
        if prefix[0] == '_':
            prefix = prefix[1:]
        value = data_object.value
        try:
            value = float(value)
        except (ValueError, TypeError):
            pass  # Keep the original value if conversion fails
        ret = self._data_object_factory(
            'extraction',
            data_object.sample_id,
            attributes={
                'tissue_prep_fluidx_id': data_object.labware_barcode,
                f'{prefix}_value': value,
                f'{prefix}_units': data_object.units,
                f'{prefix}_recorded_at': data_object.recorded_at,
                'qc_status': data_object.qc_status,
                'qc_status_decision_by': data_object.qc_status_decision_by
            }
        )
        yield ret
