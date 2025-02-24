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
    def __init__(self, data_object_factory, gap_ds):
        super().__init__(data_object_factory)
        self.gap_ds = gap_ds

    def convert(self, assembly: DataObject) -> Iterable[DataObject]:

        print(assembly.pipeline)
    
        ret = self._data_object_factory(
            'assembly',
            assembly.id,
            attributes={
            }
        )
        yield ret