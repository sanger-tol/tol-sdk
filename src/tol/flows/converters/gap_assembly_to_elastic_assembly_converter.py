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

        pipelines = self.gap_ds.get_to_many_relations(assembly)
        pipeline_atts = []
        for p in pipelines:
            pipeline_atts.append(p.attributes)

        ret = self._data_object_factory(
            'assembly',
            assembly.id,
            attributes={
                **assembly.attributes,
                'pipelines': pipeline_atts
            }
        )
        yield ret