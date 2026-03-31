# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase,
    mock
)

from tol.core import (
    core_data_object
)
from tol.google_sheets import (
    GoogleSheetDataSource
)
from tol.sources.googlesheet import googlesheet


class MockGoogleSheetDataSource(GoogleSheetDataSource):
    def _initialise_google_sheet(self):
        return mock.Mock()

    def _initialise_data(self, object_type):
        self.data[object_type] = [
            {
                'SPECIMEN_ID': 'specimen-1',
                'Sanger QC Result': 'pass',
            },
            {
                'SPECIMEN_ID': 'specimen-2',
                'Sanger QC Result': 'fail',
            },
        ]


def mock_googlesheet_data_source() -> GoogleSheetDataSource:
    gsds = MockGoogleSheetDataSource({
        'sheet_key': 'test-sheet-id',
        'mappings': {
            'specimen': {
                'worksheet_name': 'SANGER_QC',
                'columns': {
                    'id': {
                        'heading': 'SPECIMEN_ID',
                        'type': 'str'
                    },
                    'sanger_qc_result': {
                        'heading': 'Sanger QC Result',
                        'type': 'str'
                    },
                },
                'header_row': 1,
                'data_start_row': 2
            }
        }
    })
    cdo = core_data_object(gsds)
    return cdo, gsds


class TestGoogleSheetDataSource(TestCase):

    def test_attribute_types(self):
        _, gsds = mock_googlesheet_data_source()

        expected = {
            'specimen': {
                'id': 'str',
                'sanger_qc_result': 'str',
            }
        }
        self.assertEqual(expected, gsds.attribute_types)
        self.assertEqual(['specimen'], gsds.supported_types)

    def test_get_list(self):
        _, gsds = mock_googlesheet_data_source()

        ret = gsds.get_list('specimen')
        obj1 = next(ret)
        self.assertEqual('specimen-1', obj1.id)
        self.assertEqual({'sanger_qc_result': 'pass'}, obj1.attributes)

        obj2 = next(ret)
        self.assertEqual('specimen-2', obj2.id)
        self.assertEqual({'sanger_qc_result': 'fail'}, obj2.attributes)

        with self.assertRaises(StopIteration):
            next(ret)
