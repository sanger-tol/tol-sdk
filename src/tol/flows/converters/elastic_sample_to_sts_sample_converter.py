# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSampleToStsSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        yield self._data_object_factory(
            'sample',
            data_object.id,
            attributes={
                'public_name':
                    data_object.tolid_tolid.id
                    if data_object.tolid_tolid else None,
                'eln_id': data_object.benchling_eln_tissue_id,
            }
        )
