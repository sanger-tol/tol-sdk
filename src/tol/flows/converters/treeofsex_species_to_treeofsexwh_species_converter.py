# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TreeofsexSpeciesToTreeofsexwhSpeciesConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        attributes = {
            att.attribute_key.id: att.value
            for att in data_object.atts
        }

        ret = self._data_object_factory(
            'species',
            data_object.id,
            attributes=attributes,
        )
        yield ret
