# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GapAssemblyToElasticAssemblyConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, assembly: DataObject) -> Iterable[DataObject]:
        
        for p in assembly.pipelines:
            print(p)
        
        ret = self._data_object_factory(
            'assembly',
            assembly.id,
            attributes={
            }
        )
        return iter([ret])