# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import os
from datetime import datetime
from unittest import (
    TestCase
)

from tol.core import (
    core_data_object
)
from tol.google_sheets import (
    GoogleSheetDataSource
)


def google_sheet_data_source() -> GoogleSheetDataSource:
    gsds = GoogleSheetDataSource({
        'client_secrets': json.loads(os.getenv('GOOGLE_CLIENT_SECRETS')),
        'sheet_key': '1R4HX5n_kLzS9ci7c2rsrLHucjOvq0Nq3lKDq8yyBbvI',
        'mappings': {
            'object1': {
                'worksheet_name': 'Sheet1',
                'columns': {
                    'id': {
                        'heading': 'Id',
                        'type': 'int'
                    },
                    'value': {
                        'heading': 'Value',
                        'type': 'str'
                    },
                    'optional': {
                        'heading': 'Optional',
                        'type': 'str'
                    },
                    'boolean': {
                        'heading': 'Boolean',
                        'type': 'boolean'
                    },
                    'float': {
                        'heading': 'Float',
                        'type': 'float'
                    },
                    'datetime': {
                        'heading': 'Datetime',
                        'type': 'datetime'
                    }
                },
                'header_row': 2,
                'data_start_row': 4
            }
        }
    })
    cdo = core_data_object(gsds)
    return cdo, gsds


class TestGoogleSheetDataSource(TestCase):

    def test_attribute_types(self):
        _, gsds = google_sheet_data_source()
        expected = {
            'object1': {
                'id': 'int',
                'value': 'str',
                'optional': 'str',
                'boolean': 'boolean',
                'float': 'float',
                'datetime': 'datetime',
                'unmapped_column1': 'str',
            }
        }
        self.assertEqual(expected, gsds.attribute_types)
        self.assertEqual(['object1'], gsds.supported_types)

    def test_get_by_id(self):
        _, gsds = google_sheet_data_source()

        ret = gsds.get_by_id('object1', [1, 4])
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 3, 15, 12, 13, 14),
            'unmapped_column1': 'Unmapped Value 1'}, obj1.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': 5.678,
            'datetime': None,
            'unmapped_column1': None}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        _, gsds = google_sheet_data_source()

        ret = gsds.get_list('object1')
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 3, 15, 12, 13, 14),
            'unmapped_column1': 'Unmapped Value 1'}, obj1.attributes)
        obj2 = next(ret)
        self.assertEqual(2, obj2.id)
        self.assertEqual({
            'value': 'Value 2',
            'optional': None,
            'boolean': False,
            'float': None,
            'datetime': None,
            'unmapped_column1': None}, obj2.attributes)
        obj3 = next(ret)
        self.assertEqual(3, obj3.id)
        self.assertEqual({
            'value': 'Value 3',
            'optional': 'NO',
            'boolean': True,
            'float': None,
            'datetime': datetime(2030, 12, 31),
            'unmapped_column1': None}, obj3.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': 5.678,
            'datetime': None,
            'unmapped_column1': None}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)
