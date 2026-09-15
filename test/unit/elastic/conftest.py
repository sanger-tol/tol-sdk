# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import mock

import pytest

from tol.core import DefaultAttributeMetadata, core_data_object
from tol.core.operator.provenancer import ProvenanceField
from tol.core.relationship import RelationshipConfig
from tol.elastic import (
    ElasticDataSource,
    RuntimeField,
    RuntimeFields,
)
from tol.elastic.factory import _ConverterFactoriesManager


class MockElasticDataSource(ElasticDataSource):
    def _initialise_elasticsearch(self):
        self.es = mock.Mock()
        self.helpers = mock.Mock()

        self.es.indices.get_alias.return_value = {
            'test-obj-type': {'aliases': {}},
            'hidden-reltype': {'aliases': {'test-reltype': {}}}
        }
        self.index_prefix = 'test'

    def refresh_provenance_runtime_fields(self) -> None:
        # Keep unit tests isolated from alias/mapping lookups during init.
        # Build provenanced runtime fields using explicit return_type when
        # provided, otherwise default to keyword.
        runtime_fields = {}
        for object_type, fields in self.provenance_fields.items():
            object_runtime_fields = runtime_fields.setdefault(object_type, {})
            for field_name, provenance_field in fields.items():
                return_type = provenance_field.return_type or 'keyword'
                object_runtime_fields[f'{field_name}.value'] = RuntimeFields.coalesce(
                    [
                        f'{field_name}.provenance.{source_order}.value'
                        for source_order in provenance_field.source_order
                    ],
                    return_type=return_type,
                    null_wins=True,
                )

        self.runtime_fields = self._ElasticDataSource__merge_nested_dicts(
            self._base_runtime_fields,
            runtime_fields,
        )

    @property
    def attribute_types(self):
        return {
            'obj_type': {
                'field1': 'str',
                'field2': 'str',
                'field3': 'int',
                'field4': 'str',
                'field5': 'str',
                'field6': 'int',
                'field7': 'str',
                'field8': 'datetime',
                'datefield': 'datetime'},
            'reltype': {
                'field3': 'str',
                'field4': 'str',
                'datefield': 'datetime'
            }
        }


class MockAttributeMetadata(DefaultAttributeMetadata):
    def is_available_on_relationships(
            self,
            object_type: str,
            attribute_name: str) -> bool:

        if attribute_name in ['field1', 'field2']:
            return True
        return False


@pytest.fixture
def mock_elastic_data_source() -> ElasticDataSource:
    # A bit of a hacky solution, recreating most of create_elastic_datasource but using
    # the MockElasticDataSource instead
    manager = _ConverterFactoriesManager()

    eds = MockElasticDataSource(
        {
            'uri': 'test',
            'user': 'user',
            'password': 'password',
            'index_prefix': 'test'
        },
        client_factory=lambda: None,
        elastic_converter_factory=manager.elastic_api_converter_factory,
        data_object_converter_factory=manager.data_object_converter_factory,
        data_object_update_converter_factory=manager.data_object_update_converter_factory,
        relationship_cfg={
            'obj_type': RelationshipConfig(
                to_one={
                    'relationship': 'reltype',
                    'another_relationship': 'reltype'
                },
                to_many={'children': 'reltype'}
            ),
            'reltype': RelationshipConfig(
                to_one={'parent': 'obj_type'}
            )
        },
        runtime_fields={
            'obj_type': {
                'field7': RuntimeField(
                    field_type='keyword',
                    dependencies=[],
                    function_body="emit('Hello')"
                ),
                'field8': RuntimeField(
                    field_type='date',
                    dependencies=['datefield'],
                    function_body="emit(doc['datefield'].value.toEpochMilli())"
                )
            }
        },
        attribute_metadata=MockAttributeMetadata,
        provenance_fields={
            'obj_type': {
                'field5': ProvenanceField(
                    source_order=['source_1', 'source_2'],
                    return_type='keyword'
                ),
                'relationship.id': ProvenanceField(
                    source_order=['source_1', 'source_2'],
                    return_type=None
                )
            },
            'reltype': {
                'parent.id': ProvenanceField(
                    source_order=['source_1', 'source_2'],
                    return_type=None
                )
            }
        }
    )
    manager.data_source = eds
    core_data_object(eds)
    return eds


@pytest.fixture
def mock_lazy_elastic_data_source(
    mock_elastic_data_source: ElasticDataSource
) -> ElasticDataSource:
    mock_elastic_data_source.lazy_fetch = True
    return mock_elastic_data_source
