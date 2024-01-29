# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DefaultAttributeMetadata
)


class TestAttributeMetadata(TestCase):
    def test_get_display_name(self):
        am = DefaultAttributeMetadata()
        self.assertEqual('ID', am.get_display_name('object_type', 'id'))
        self.assertEqual('ToLQC Status', am.get_display_name('object_type', 'tolqc_status'))
        self.assertEqual('Random Words', am.get_display_name('object_type', 'random_words'))

    def test_get_description(self):
        am = DefaultAttributeMetadata()
        self.assertIsNone(am.get_description('object_type', 'attribute_name'))

    def test_is_attribute_available_on_relationships(self):
        am = DefaultAttributeMetadata()
        self.assertTrue(am.is_available_on_relationships(
            'object_type', 'attribute_name'
        ))

    def test_get_cardinality(self):
        am = DefaultAttributeMetadata()
        self.assertIsNone(am.get_cardinality('object_type', 'attribute_name'))
