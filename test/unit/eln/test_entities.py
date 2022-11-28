# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import

from unittest import TestCase

from tol.eln import flatten_entity


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
        print(flatten_entity(entity))
        self.assertEqual(expected, flatten_entity(entity))
