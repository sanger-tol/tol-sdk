# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticTolidToElasticSampleUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        if data_object.tolid_species is not None and data_object.tolid_specimen is not None:
            species = data_object.to_one_relationships['tolid_species']
            specimen = data_object.to_one_relationships['tolid_specimen']
            yield (
                None,
                {
                    'tolid_tolid': {'id': data_object.id},
                    'sts_species.id':
                        data_object.requested_taxonomy_id
                        if data_object.requested_taxonomy_id is not None
                        else species.id,
                    'sts_specimen.id': specimen.id
                }
            )
