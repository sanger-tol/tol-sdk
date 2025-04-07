# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Dict
from unittest import TestCase

from tol.core import DataSource, DataSourceFilter, DefaultAttributeMetadata
from tol.core.operator import Relational
from tol.core.operator._filterable import _Filterable
from tol.core.relationship import RelationshipConfig


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


class _TestDataSourceAttributes(DataSource, Relational, _Filterable):
    def __init__(self, config: Dict):
        super().__init__(
            config,
            expected=[],
            attribute_metadata=_TestAttributeMetadata)

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        return {
            'object_type1': RelationshipConfig(to_one={'rel1': 'object_type2'})
        }

    def get_to_one_relation(self, source, relationship_name, session=None):
        raise NotImplementedError()

    def get_to_many_relations(self, source, relationship_name, session=None):
        raise NotImplementedError()

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

    def test_filter(self):
        ds = _TestDataSourceAttributes({})

        f = DataSourceFilter()
        f.and_ = {
            'attribute1': {
                'eq': {
                    'value': 'test_value'
                }
            },
            'rel1.attribute4': {
                'lt': {
                    'value': '1 year ago'
                }
            }
        }
        processed_filter = ds._preprocess_filter('object_type1', f)
        self.assertEqual('test_value', processed_filter.and_['attribute1']['eq']['value'])
        # Assert that the relative date has been preprocessed into a datetime with the correct year
        last_year = datetime.now().year - 1
        self.assertEqual(last_year, processed_filter.and_['rel1.attribute4']['lt']['value'].year)
