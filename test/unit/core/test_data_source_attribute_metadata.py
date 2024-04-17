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


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['attribute']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    def get_list(self, object_type: str, *args, **kwargs):
        CoreDataObject = self.data_object_factory  # noqa N806
        return [
            CoreDataObject(
                'attribute',
                str(i),
                attributes={
                    'display_name': f'Display name {i}',
                    'available_on_relationships': False if i == 15 else True,
                    'authoritative': True if i == 15 else False,
                    'description': f'Description {i}',
                    'object_type': 'object_type1',
                    'name': f'attribute_{i}'
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
        dsam = data_source_attribute_metadata(mock_ds)()
        dsam.host = _MockDataSourceHost({})
        # Given attributes for attribute15
        self.assertEqual('Display name 15', dsam.get_display_name('object_type1', 'attribute_15'))
        self.assertTrue(dsam.is_authoritative('object_type1', 'attribute_15'))
        self.assertFalse(dsam.is_available_on_relationships('object_type1', 'attribute_15'))
        self.assertEqual('Description 15', dsam.get_description('object_type1', 'attribute_15'))
        self.assertEqual(2, dsam.get_cardinality('object_type1', 'attribute_15'))
        # Given attributes for attribute16
        self.assertEqual('Display name 16', dsam.get_display_name('object_type1', 'attribute_16'))
        self.assertFalse(dsam.is_authoritative('object_type1', 'attribute_16'))
        self.assertTrue(dsam.is_available_on_relationships('object_type1', 'attribute_16'))
        self.assertEqual('Description 16', dsam.get_description('object_type1', 'attribute_16'))
        self.assertEqual(600, dsam.get_cardinality('object_type1', 'attribute_16'))
        # Given attributes for attribute22 (not given so use defaults)
        self.assertEqual('Attribute 22', dsam.get_display_name('object_type1', 'attribute_22'))
        self.assertFalse(dsam.is_authoritative('object_type1', 'attribute_22'))
        self.assertFalse(dsam.is_available_on_relationships('object_type1', 'attribute_22'))
        self.assertIsNone(dsam.get_description('object_type1', 'attribute_22'))
        self.assertIsNone(dsam.get_cardinality('object_type1', 'attribute_12'))
