# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import mock

import pytest

from tol.core import DataSource, DefaultAttributeMetadata, core_data_object
from tol.core.relationship import RelationshipConfig
from tol.elastic import ElasticDataSource, RuntimeField, ElasticApiConverter
from tol.elastic.parser import DefaultParser


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
    # COPIED FROM FACTORY.PY
    class _ConverterFactory:
        """
        Manages the instantiation of `ElasticApiConverter`
        """
        __slots__ = ['__data_source']
        __data_source: DataSource | None  

        def __init__(self) -> None:
            # The converter factory is instantisated before the data source, so this must be assigned
            # after initialisation. Therefore, if `None`, the data source hasn't been instantiate yet
            self.__data_source = None

        @property
        def data_source(self) -> DataSource | None:
            """
            Fetch the data source, or `None` if it hasn't been instantiated yet
            """
            return self.__data_source

        @data_source.setter
        def data_source(self, data_source: DataSource) -> None:
            self.__data_source = data_source

        def elastic_converter_factory(self) -> ElasticApiConverter:
            # TODO CHECK NOT NONE OR USE DICT FROM BEFORE
            parser = DefaultParser(self.data_source)
            return ElasticApiConverter(parser)

    manager = _ConverterFactory()

    eds = MockElasticDataSource(
        {
            'uri': 'test',
            'user': 'user',
            'password': 'password',
            'index_prefix': 'test'
        },
        client_factory=lambda: None,
        elastic_converter_factory=manager.elastic_converter_factory,
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
    manager.data_source = eds
    core_data_object(eds)
    return eds


@pytest.fixture
def mock_lazy_elastic_data_source(
    mock_elastic_data_source: ElasticDataSource
) -> ElasticDataSource:
    mock_elastic_data_source.lazy_fetch = True
    return mock_elastic_data_source
