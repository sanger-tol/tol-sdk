# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DefaultAttributeMetadata
)


class TestAttributeMetadata(TestCase):
    def test_formatting(self):
        am = DefaultAttributeMetadata()
        self.assertEqual('ID', am.format_string('id'))
        self.assertEqual('ToLQC Status', am.format_string('tolqc_status'))
        self.assertEqual('Random Words', am.format_string('random_words'))

    def test_get_description(self):
        am = DefaultAttributeMetadata()
        self.assertIsNone(am.get_attribute_description('object_type', 'attribute_name'))

    def test_is_attribute_available_on_relationships(self):
        am = DefaultAttributeMetadata()
        self.assertTrue(am.is_attribute_available_on_relationships(
            'object_type', 'attribute_name'
        ))

    def test_get_cardinality(self):
        am = DefaultAttributeMetadata()
        self.assertIsNone(am.get_cardinality('object_type', 'attribute_name'))
