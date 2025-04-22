# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GapAssemblyToElasticAssemblyAnalysisConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert_details(self, assembly: DataObject) -> Iterable[DataObject]:
        return {
            d.id.replace(' ', '_').lower(): d.info
            for d in assembly.assembly_details
        }

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:

        for p in data_object.pipelines:
            ret = self._data_object_factory(
                'assembly_analysis',
                f'{data_object.id}_{p.id}',
                attributes={
                    'analysis': p.analysis,
                    'results': p.results,
                    's3': p.s3,
                    'lustre_path_analysis': p.lustre_path_analysis,
                },
                to_one={
                    'assembly': self._data_object_factory(
                        'assembly',
                        data_object.id
                    ),
                    'species': self._data_object_factory(
                        'species',
                        str(data_object.taxon_id)
                    ),
                }
            )
            yield ret
