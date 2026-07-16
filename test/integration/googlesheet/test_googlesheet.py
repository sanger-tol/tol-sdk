# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import os
from unittest import (
    TestCase
)

from tol.google_sheets import (
    GoogleSheetDataSource
)
from tol.sources.googlesheet import googlesheet


SYSTEM_TEST_ASSETS_SHEET_KEY = '1R4HX5n_kLzS9ci7c2rsrLHucjOvq0Nq3lKDq8yyBbvI'


def googlesheet_data_source() -> GoogleSheetDataSource:
    mappings = {
        'specimen': {
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
            },
            'header_row': 2,
            'data_start_row': 4
        }
    }

    gsds = googlesheet(
        googlesheet_id=SYSTEM_TEST_ASSETS_SHEET_KEY,
        mappings=mappings,
    )
    return gsds


class TestGoogleSheetDataSource(TestCase):

    def test_attribute_types(self):
        gsds = googlesheet_data_source()
        self.assertIsInstance(gsds, GoogleSheetDataSource)

        expected = {
            'specimen': {
                'id': 'int',
                'value': 'str',
            }
        }
        self.assertEqual(expected, gsds.attribute_types)
        self.assertEqual(['specimen'], gsds.supported_types)

    def test_get_list(self):
        gsds = googlesheet_data_source()

        rows = list(gsds.get_list('specimen'))
        self.assertGreaterEqual(len(rows), 1)

        obj1 = rows[0]
        self.assertEqual('specimen', obj1.type)
        self.assertIsInstance(obj1.id, int)
        self.assertIn('value', obj1.attributes)
