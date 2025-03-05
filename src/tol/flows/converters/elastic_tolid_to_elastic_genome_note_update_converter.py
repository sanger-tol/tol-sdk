# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticTolidToElasticGenomeNoteUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        species = data_object.to_one_relationships['tolid_species']
        yield (
            None,
            {
                'gn_species': {'id': species.id},
                'gn_tolid.id': data_object.id
            }
        )
