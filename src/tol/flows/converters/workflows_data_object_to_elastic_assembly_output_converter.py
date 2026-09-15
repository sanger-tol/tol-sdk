# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from .workflows_data_object_to_elastic_assembly_analysis_converter import (
    WorkflowsDataObjectToElasticAssemblyAnalysisConverter
)
from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...utils import convert_s3_to_https


class WorkflowsDataObjectToElasticAssemblyOutputConverter(
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

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        attributes = {
            'url': convert_s3_to_https(data_object.url),
            'file_format': data_object.file_format,
            'path': data_object.path,
            'description': data_object.description
        }

        relationships = {}
        if data_object.assembly_accession:
            relationships['assembly'] = self._data_object_factory(
                'assembly',
                data_object.assembly_accession
            )
        if data_object.tax_id:
            relationships['species'] = self._data_object_factory(
                'species',
                data_object.tax_id
            )
        analysis_id = WorkflowsDataObjectToElasticAssemblyAnalysisConverter.analysis_id(
            data_object
        )
        if analysis_id:
            relationships['assembly_analysis'] = self._data_object_factory(
                'assembly_analysis',
                analysis_id
            )

        ret = self._data_object_factory(
            'assembly_output',
            data_object.id,
            attributes=attributes,
            to_one=relationships
        )
        yield ret
