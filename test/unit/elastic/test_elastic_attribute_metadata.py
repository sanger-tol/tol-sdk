# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.elastic import (
    ElasticAttributeMetadata,
)


class TestElasticDataSource(TestCase):

    def test_attribute_available_on_relationships(self):
        class _TestElasticAttributeMetadata(ElasticAttributeMetadata):
            attribute_meta = {
                'obj_type': {'field1': {'available_on_relationships': True}}
            }
        am = _TestElasticAttributeMetadata()
        self.assertTrue(am.is_attribute_available_on_relationships('obj_type', 'field1'))
        self.assertFalse(am.is_attribute_available_on_relationships('obj_type', 'field2'))
        self.assertFalse(am.is_attribute_available_on_relationships('reltype', 'field3'))
