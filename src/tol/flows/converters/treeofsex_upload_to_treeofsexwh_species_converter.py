# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class TreeofsexUploadToTreeofsexwhSpeciesConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        ret = self._data_object_factory(
            'species',
            data_object.species,
            attributes={
                data_object.key: [
                    {
                        'value': data_object.value,
                        'source': data_object.reference,
                    }
                ]
            }
        )
        yield ret
