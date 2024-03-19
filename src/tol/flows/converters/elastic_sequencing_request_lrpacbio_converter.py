# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class ElasticSequencingRequestLrpacbioConverter(
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

        if ('library_remaining' in data_object.attributes
                and data_object.attributes['library_remaining'] is not None):
            target_attributes['library_remaining'] = self._clean_attribute(
                data_object.attributes['library_remaining']
            )
        if ('library_remaining_oplc' in data_object.attributes
                and data_object.attributes['library_remaining_oplc'] is not None):
            target_attributes['library_remaining_oplc'] = self._clean_attribute(
                data_object.attributes['library_remaining_oplc'])

        ret = self._data_object_factory(
            'sequencing_request',
            data_object.id,
            attributes=target_attributes
        )
        return iter([ret])
