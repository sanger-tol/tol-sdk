# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class LrpacbioSequencingRequestToElasticSequencingRequestConverter(
        DataObjectToDataObjectOrUpdateConverter):

    def _clean_attribute(self, value):
        if isinstance(value, str):
            try:
                return max(float(value), 0.0)
            except ValueError:
                return None
        else:
            return max(value, 0.0)

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        target_attributes = {}

        for field in ['library_remaining', 'library_remaining_oplc', 'estimated_max_oplc']:
            if (field in data_object.attributes
                    and data_object.attributes[field] is not None):
                target_attributes[field] = self._clean_attribute(
                    data_object.attributes[field]
                )

        ret = self._data_object_factory(
            'sequencing_request',
            data_object.id,
            attributes=target_attributes
        )
        return iter([ret])
