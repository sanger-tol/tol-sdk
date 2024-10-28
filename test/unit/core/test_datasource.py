# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict
from unittest import TestCase

import pytest

from tol.core import DataSource, DataSourceError, DefaultAttributeMetadata
from tol.core.datasource_error import NoDataObjectFactoryError
from tol.core.operator import PageGetter


class _TestDataSourceExpected(DataSource):
    def __init__(self, config: Dict):
        super().__init__(config, expected=['field1', 'field2'])

    @property
    def supported_types(self):
        raise NotImplementedError()

    @property
    def attribute_types(self):
        raise NotImplementedError()


ERROR_MESSAGE = "I don't like this."


class _TestDataSourceNoExpected(DataSource, PageGetter):
    def __init__(self, config: Dict):
        super().__init__(config, expected=[])

    def get_list_page(self, object_type: str, *args, **kwargs):
        return [{
            'hello': 'world'
        }]

    @property
    def supported_types(self):
        raise NotImplementedError()

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _TestAttributeMetadata(DefaultAttributeMetadata):
    def get_display_name(self, object_type: str, input_string: str) -> str:
        return input_string.upper()

    def is_available_on_relationships(self, object_type, attribute_name):
        if object_type == 'object_type1':
            return True
        return False

    def is_authoritative(self, object_type, attribute_name):
        if object_type == 'object_type1':
            return True
        return False

    def get_cardinality(self, object_type, attribute_name):
        if object_type == 'object_type1':
            return 1000
        return 5

    def get_description(self, object_type, attribute_name):
        return f'Interesting {attribute_name}'

    def get_source(self, object_type, attribute_name):
        return 'test_source'


class _TestDataSourceAttributes(DataSource):
    def __init__(self, config: Dict):
        super().__init__(
            config,
            expected=[],
            attribute_metadata=_TestAttributeMetadata)

    @property
    def supported_types(self):
        return ['object_type1', 'object_type2']

    @property
    def attribute_types(self):
        return {
            'object_type1': {
                'attribute1': 'str',
                'attribute2': 'int'
            },
            'object_type2': {
                'attribute3': 'str',
                'attribute4': 'datetime'
            }
        }


class TestDataSource(TestCase):
    def test_expected_parameters(self):
        with self.assertRaises(DataSourceError):
            _TestDataSourceExpected({})
        with self.assertRaises(DataSourceError):
            _TestDataSourceExpected({'field1': 'value1'})
        _TestDataSourceExpected({'field1': 'value1', 'field2': 'value2'})

    def test_no_expected_parameters(self):
        _TestDataSourceNoExpected({})
        _TestDataSourceNoExpected({'field1': 'value1'})
        _TestDataSourceNoExpected({'field1': 'value1', 'field2': 'value2'})

    def test_supported_method_no_exception(self):
        _TestDataSourceNoExpected({}).get_list_page('test')

    def test_no_object_factory(self):
        """
        Not setting the data_object_factory -> MisconfiguredDataSourceException
        """

        with pytest.raises(NoDataObjectFactoryError):
            _TestDataSourceNoExpected({}).data_object_factory

    def test_attributes(self):
        ds = _TestDataSourceAttributes({})
        self.assertEqual(
            ds.attribute_metadata,
            {
                'object_type1': {
                    'attribute1': {
                        'python_type': 'str',
                        'display_name': 'ATTRIBUTE1',
                        'description': 'Interesting attribute1',
                        'cardinality': 1000,
                        'available_on_relationships': True,
                        'authoritative': True,
                        'source': 'test_source'
                    },
                    'attribute2': {
                        'python_type': 'int',
                        'display_name': 'ATTRIBUTE2',
                        'description': 'Interesting attribute2',
                        'cardinality': 1000,
                        'available_on_relationships': True,
                        'authoritative': True,
                        'source': 'test_source'
                    }
                },
                'object_type2': {
                    'attribute3': {
                        'python_type': 'str',
                        'display_name': 'ATTRIBUTE3',
                        'description': 'Interesting attribute3',
                        'cardinality': 5,
                        'available_on_relationships': False,
                        'authoritative': False,
                        'source': 'test_source'
                    },
                    'attribute4': {
                        'python_type': 'datetime',
                        'display_name': 'ATTRIBUTE4',
                        'description': 'Interesting attribute4',
                        'cardinality': 5,
                        'available_on_relationships': False,
                        'authoritative': False,
                        'source': 'test_source'
                    }
                }
            }
        )
