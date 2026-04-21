# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GapAssemblyToElasticAssemblyAnalysisConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

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
