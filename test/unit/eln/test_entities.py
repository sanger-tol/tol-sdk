# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import

from unittest import TestCase

from tol.eln import (
    convert_sts_entity_to_eln_entity_fields,
    flatten_entity
)


class TestEntities(TestCase):

    def test_flatten_entity(self):

        entity = {
            'field1': 'value1',
            'field2': 'value2',
            'list': [{'subfield1': 'subvalue1',
                      'subfield2': 'subvalue2'},
                     {'subfield1': 'subvalue3',
                      'subfield2': 'subvalue4'}],
            'dict': {'dictfield1': 'dictvalue1',
                     'dictfield2': 'dictvalue2'}
        }

        expected = {
            'field1': 'value1',
            'field2': 'value2',
            'list_0_subfield1': 'subvalue1',
            'list_0_subfield2': 'subvalue2',
            'list_1_subfield1': 'subvalue3',
            'list_1_subfield2': 'subvalue4',
            'dict_dictfield1': 'dictvalue1',
            'dict_dictfield2': 'dictvalue2'
        }
        self.assertEqual(expected, flatten_entity(entity))

    def test_convert_entity(self):
        entity = {
            'field1': 'value1',
            'field2': 'value2',
            'list': [{'subfield1': 'subvalue1',
                      'subfield2': 'subvalue2'},
                     {'subfield1': 'subvalue3',
                      'subfield2': 'subvalue4'}],
            'dict': {'dictfield1': 'dictvalue1',
                     'dictfield2': 'dictvalue2'}
        }

        mapping = {
            'field_mappings': {
                'field1': 'newfield1',
                'list_0_subfield1': 'newfield2',
                'list_0_subfield2': 'newfield3',
                'list_1_subfield1': 'newfield4',
                'dict_dictfield1': 'newfield5'
            }
        }

        expected = {
            'newfield1': 'value1',
            'newfield2': 'subvalue1',
            'newfield3': 'subvalue2',
            'newfield4': 'subvalue3',
            'newfield5': 'dictvalue1',
        }

        self.assertEqual(expected, convert_sts_entity_to_eln_entity_fields(entity, mapping))
