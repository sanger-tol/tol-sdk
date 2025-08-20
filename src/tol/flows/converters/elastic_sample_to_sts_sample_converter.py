# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSampleToStsSampleConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        eln_updated_at = data_object.sts_eln_updated_at
        if not eln_updated_at \
                and data_object.benchling_eln_tissue_id is not None:
            eln_updated_at = datetime.now()
        yield self._data_object_factory(
            'sample',
            data_object.id,
            attributes={
                'public_name':
                    data_object.tolid_tolid.id
                    if data_object.tolid_tolid else None,
                'eln_id': data_object.benchling_eln_tissue_id,
                'ep_exported': True if data_object.benchling_eln_tissue_id else False,
                'eln_updated_at': eln_updated_at,
            }
        )
