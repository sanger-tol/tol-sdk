# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable, Optional

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class WorkflowsDataObjectToElasticAssemblyAnalysisConverter(
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
        analysis_id = f'{data_object.assembly_accession}_{data_object.workflow_run.workflow.name}'
        busco_lineage = (data_object.extra_identifiers or {}).get('busco_lineage')
        if busco_lineage:
            analysis_id = f'{analysis_id}_{busco_lineage}'

        attributes = {
            'workflow_name': data_object.workflow_run.workflow.name,
            'workflow_version': data_object.workflow_run.workflow.version,
            'workflow_description': data_object.workflow_run.workflow.description,
            'start_date': data_object.workflow_run.started_at,
            'end_date': data_object.workflow_run.ended_at
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

        ret = self._data_object_factory(
            'assembly_analysis',
            analysis_id,
            attributes=attributes,
            to_one=relationships
        )
        yield ret

    @classmethod
    def analysis_id(cls, data_object_instance: DataObject) -> Optional[str]:
        run = data_object_instance.output_workflow_run
        if (
            not run
            or not run.workflow
            or not data_object_instance.assembly_accession
        ):
            return None
        result = f'{data_object_instance.assembly_accession}_{run.workflow.name}'
        if data_object_instance.run_accession:
            result = f'{result}_{data_object_instance.run_accession}'
        busco_lineage = (data_object_instance.extra_identifiers or {}).get('busco_lineage')
        if busco_lineage:
            result = f'{result}_{busco_lineage}'
        return result
