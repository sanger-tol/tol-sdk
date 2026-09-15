# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    WorkflowsDataObjectToElasticAssemblyAnalysisConverter
)


class _MockDataSourceSource(DataSource, Relational):

    @property
    def supported_types(self):
        return ['workflow', 'workflow_run', 'data_object']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_workflow_run = RelationshipConfig()
        rc_workflow_run.to_one = {
            'workflow': 'workflow'
        }
        rc_data_object = RelationshipConfig()
        rc_data_object.to_one = {
            'output_workflow_run': 'workflow_run'
        }
        return {
            'workflow_run': rc_workflow_run,
            'data_object': rc_data_object
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass


class _MockDataSourceDestination(DataSource, Relational):

    @property
    def supported_types(self):
        return ['assembly', 'assembly_analysis', 'assembly_output', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_assembly_analysis = RelationshipConfig()
        rc_assembly_analysis.to_one = {
            'assembly': 'assembly',
            'species': 'species'
        }
        rc_assembly_output = RelationshipConfig()
        rc_assembly_output.to_one = {
            'assembly': 'assembly',
            'species': 'species',
            'assembly_analysis': 'assembly_analysis'
        }
        return {
            'assembly_analysis': rc_assembly_analysis,
            'assembly_output': rc_assembly_output
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass


class TestWorkflowsDataObjectToElasticAssemblyAnalysisConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceSource(config={})
        destination = _MockDataSourceDestination(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = WorkflowsDataObjectToElasticAssemblyAnalysisConverter(
            data_object_factory=destination.data_object_factory,
            config=WorkflowsDataObjectToElasticAssemblyAnalysisConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806

        workflow = CoreDataObject(
            'workflow',
            'curation-workflow',
            attributes={
                'name': 'curation-workflow',
                'version': '1.0.0',
                'description': 'Pipeline run'
            }
        )
        workflow_run = CoreDataObject(
            'workflow_run',
            'wf-run-1',
            to_one={
                'workflow': workflow
            },
            attributes={
                'started_at': '2026-08-01T11:00:00Z',
                'ended_at': '2026-08-01T12:00:00Z'
            }
        )

        obj1 = CoreDataObject(
            id_='wf-1',
            type_='data_object',
            attributes={
                'assembly_accession': 'GCA_123456',
                'tax_id': '9606',
                'extra_identifiers': {
                    'busco_lineage': 'metazoa_odb10'
                }
            },
            to_one={
                'output_workflow_run': workflow_run
            }
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)

        self.assertEqual('GCA_123456_curation-workflow_metazoa_odb10', ret1.id)
        self.assertEqual('assembly_analysis', ret1.type)
        self.assertEqual(ret1.attributes, {
            'workflow_name': 'curation-workflow',
            'workflow_version': '1.0.0',
            'workflow_description': 'Pipeline run',
            'start_date': '2026-08-01T11:00:00Z',
            'end_date': '2026-08-01T12:00:00Z'
        })
        self.assertEqual(ret1.to_one_relationships['assembly'].id, 'GCA_123456')
        self.assertEqual(ret1.to_one_relationships['species'].id, '9606')

        with self.assertRaises(StopIteration):
            next(converteds)

    def test_analysis_id(self):

        source = _MockDataSourceSource(config={})
        core_data_object(source)

        CoreDataObject = source.data_object_factory  # noqa N806
        workflow = CoreDataObject(
            'workflow',
            'curation-workflow',
            attributes={
                'name': 'curation-workflow',
                'version': '1.0.0',
                'description': 'Pipeline run'
            }
        )
        workflow_run = CoreDataObject(
            'workflow_run',
            'wf-run-1',
            to_one={
                'workflow': workflow
            },
            attributes={
                'started_at': '2026-08-01T11:00:00Z',
                'ended_at': '2026-08-01T12:00:00Z'
            }
        )
        obj1 = CoreDataObject(
            id_='out-1',
            type_='data_object',
            attributes={
                'assembly_accession': 'GCA_123456',
                'run_accession': 'ERR000001',
                'extra_identifiers': {
                    'busco_lineage': 'metazoa_odb10'
                }
            },
            to_one={
                'output_workflow_run': workflow_run
            }
        )

        ret1 = WorkflowsDataObjectToElasticAssemblyAnalysisConverter.analysis_id(obj1)
        self.assertEqual(
            'GCA_123456_curation-workflow_ERR000001_metazoa_odb10',
            ret1
        )

    def test_analysis_id_returns_none_without_run(self):

        source = _MockDataSourceSource(config={})
        core_data_object(source)

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='out-1',
            type_='data_object',
            attributes={
                'assembly_accession': 'GCA_123456',
                'output_workflow_run': None
            }
        )

        ret1 = WorkflowsDataObjectToElasticAssemblyAnalysisConverter.analysis_id(obj1)
        self.assertIsNone(ret1)
