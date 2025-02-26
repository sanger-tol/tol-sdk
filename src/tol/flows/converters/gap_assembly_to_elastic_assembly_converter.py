# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from uuid import uuid4

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
        pipeline_atts = {}
        for p in pipelines:
            prefix = p.id
            pipeline_atts = {
                f'{prefix}_analysis': p.analysis,
                f'{prefix}_results': p.results,
                f'{prefix}_s3': p.s3,
                f'{prefix}_lustre_path_analysis': p.lustre_path_analysis,
                **pipeline_atts,
            }
            
        to_one_relations = {
            'species': self._data_object_factory(
                'species',
                str(assembly.taxon_id)
            ),
        }

        ret = self._data_object_factory(
            'assembly',
            assembly.id,
            attributes={
                **pipeline_atts,
                'project': assembly.project,
                'assembly_name': assembly.assembly_name,
                'results': assembly.results,
                'image_url': assembly.image_url,
                'image_caption': assembly.image_caption,
                'lustre_path_analysis_base': assembly.lustre_path_analysis_base,
                'lustre_path_assembly': assembly.lustre_path_assembly,
                'lustre_path_species': assembly.lustre_path_species,
            },
            to_one=to_one_relations
        )
        yield ret
