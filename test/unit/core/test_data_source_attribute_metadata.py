# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.core.data_source_attribute_metadata import (
    data_source_attribute_metadata
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['data_source_config', 'data_source_config_attribute']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    def get_one(self, object_type: str, id_: str):
        return self.data_object_factory(
            'data_source_config',
            17
        )

    def get_list(self, object_type: str, *args, **kwargs):
        raise NotImplementedError()

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        return {
            'data_source_config_attribute': RelationshipConfig(
                to_one={'data_source_config': 'data_source_config'}
            ),
            'data_source_config': RelationshipConfig(
                to_many={'data_source_config_attributes': 'data_source_config_attribute'}
            )
        }

    def get_to_one_relation(self, source, relationship_name, session=None):
        raise NotImplementedError()

    def get_to_many_relations(self, source, relationship_name, session=None):
        return [
            self.data_object_factory(
                'data_source_config_attribute',
                str(i),
                attributes={
                    'display_name': f'Display name {i}',
                    'available_on_relationships': False if i == 15 else True,
                    'is_authoritative': True if i == 15 else False,
                    'description': f'Description {i}',
                    'object_type': 'object_type1',
                    'name': f'attribute_{i}',
                    'acts_as': 'status' if i == 15 else None,
                    'source': 'source1' if i != 15 else None,
                    'source_order': ['source1', 'source2'] if i == 15 else None,
                })
            for i in range(20)
        ]


class _MockDataSourceHost(DataSource):
    @property
    def supported_types(self):
        return ['object_type1']

    @property
    def attribute_types(self):
        return {
            'object_type1': {
                'attribute_15': 'str',
                'attribute_16': 'str'
            }
        }

    def get_stats(self, object_type: str, *args, **kwargs):
        return {
            'stats': {
                'attribute_15': {
                    'cardinality': 2
                },
                'attribute_16': {
                    'cardinality': 600
                }
            }
        }


class TestDataSourceAttributeMetadata(TestCase):
    def test_attribute_metadata(self):
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)
        mock_ds_config = mock_ds.get_one('data_source_config', 17)
        dsam = data_source_attribute_metadata(mock_ds_config)()
        dsam.host = _MockDataSourceHost({})
        # Given attributes for attribute15
        self.assertEqual('Display name 15', dsam.get_display_name('object_type1', 'attribute_15'))
        self.assertTrue(dsam.is_authoritative('object_type1', 'attribute_15'))
        self.assertFalse(dsam.is_available_on_relationships('object_type1', 'attribute_15'))
        self.assertEqual('Description 15', dsam.get_description('object_type1', 'attribute_15'))
        self.assertEqual(2, dsam.get_cardinality('object_type1', 'attribute_15'))
        self.assertEqual('status', dsam.get_acts_as('object_type1', 'attribute_15'))
        self.assertIsNone(dsam.get_source('object_type1', 'attribute_15'))
        self.assertEqual(['source1', 'source2'], dsam.get_source_order('object_type1', 'attribute_15'))
        # Given attributes for attribute16
        self.assertEqual('Display name 16', dsam.get_display_name('object_type1', 'attribute_16'))
        self.assertFalse(dsam.is_authoritative('object_type1', 'attribute_16'))
        self.assertTrue(dsam.is_available_on_relationships('object_type1', 'attribute_16'))
        self.assertEqual('Description 16', dsam.get_description('object_type1', 'attribute_16'))
        self.assertEqual(600, dsam.get_cardinality('object_type1', 'attribute_16'))
        self.assertIsNone(dsam.get_acts_as('object_type1', 'attribute_16'))
        self.assertEqual('source1', dsam.get_source('object_type1', 'attribute_16'))
        self.assertIsNone(dsam.get_source_order('object_type1', 'attribute_16'))
        # Given attributes for attribute22 (not given so use defaults)
        self.assertEqual('Attribute 22', dsam.get_display_name('object_type1', 'attribute_22'))
        self.assertFalse(dsam.is_authoritative('object_type1', 'attribute_22'))
        self.assertFalse(dsam.is_available_on_relationships('object_type1', 'attribute_22'))
        self.assertIsNone(dsam.get_description('object_type1', 'attribute_22'))
        self.assertIsNone(dsam.get_cardinality('object_type1', 'attribute_22'))
        self.assertIsNone(dsam.get_acts_as('object_type1', 'attribute_22'))
        self.assertIsNone(dsam.get_source('object_type1', 'attribute_22'))
        self.assertIsNone(dsam.get_source_order('object_type1', 'attribute_22'))
