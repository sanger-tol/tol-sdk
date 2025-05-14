# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticSequencingRequestToElasticRunDataUpdateConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        to_ones = {}
        if 'benchling_sample' in data_object.to_one_relationships:
            sample = data_object.to_one_relationships['benchling_sample']
            if sample is not None:
                to_ones['benchling_sample'] = self._data_object_factory(
                    'sample',
                    sample.id
                )
        if 'benchling_extraction' in data_object.to_one_relationships:
            extraction = data_object.to_one_relationships['benchling_extraction']
            if extraction is not None:
                to_ones['benchling_extraction'] = self._data_object_factory(
                    'extraction',
                    extraction.id
                )
        yield (None, to_ones | {
            'mlwh_sequencing_request.id': data_object.id})  # The candidate key
