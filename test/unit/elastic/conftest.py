import pytest
from unittest import mock

from tol.core import DefaultAttributeMetadata, core_data_object
from tol.core.relationship import RelationshipConfig
from tol.elastic import ElasticDataSource, RuntimeField


class MockElasticDataSource(ElasticDataSource):
    def _initialise_elasticsearch(self):
        self.es = mock.Mock()
        self.helpers = mock.Mock()

        self.es.indices.get_alias.return_value = {
            'test-obj-type': {'aliases': {}},
            'hidden-reltype': {'aliases': {'test-reltype': {}}}
        }
        self.index_prefix = 'test'

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
    eds = MockElasticDataSource(
        {
            'uri': 'test',
            'user': 'user',
            'password': 'password',
            'index_prefix': 'test'
        },
        relationship_cfg={
            'obj_type': RelationshipConfig(
                to_one={'relationship': 'reltype'},
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
        attribute_metadata=MockAttributeMetadata
    )
    core_data_object(eds)
    return eds

@pytest.fixture
def mock_lazy_elastic_data_source() -> ElasticDataSource:
    eds = mock_elastic_data_source()
    eds.lazy_fetch = True

    return eds
