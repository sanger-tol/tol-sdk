# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
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


class MockGoogleSheetDataSource(GoogleSheetDataSource):
    def _initialise_google_sheet(self):
        return mock.Mock()

    def _initialise_data(self, object_type):
        self.data[object_type] = [
            {
                'Id': 1,
                'Value': 'Value 1',
                'Optional': 'YES'
            },
            {
                'Id': 2,
                'Value': 'Value 2',
                'Optional': None
            },
            {
                'Id': 3,
                'Value': 'Value 3',
                'Optional': 'NO'
            },
            {
                'Id': 4,
                'Value': 'Value 4',
                'Optional': None
            }

        ]


def mock_google_sheet_data_source() -> GoogleSheetDataSource:
    gsds = MockGoogleSheetDataSource({
        'client_secrets': {},
        'sheet_key': 'MOCK',
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
                    }
                },
                'header_row': 2,
                'data_start_row': 4
            }
        }
    })
    core_data_object_mock = core_data_object(gsds)
    return core_data_object_mock, gsds


class TestGoogleSheetDataSource(TestCase):

    def test_attribute_types(self):
        _, gsds = mock_google_sheet_data_source()
        expected = {
            'object1': {
                'id': 'int',
                'value': 'str',
                'optional': 'str'
            }
        }
        self.assertEqual(expected, gsds.attribute_types)
        self.assertEqual(['object1'], gsds.supported_types)

    def test_get_by_id(self):
        _, gsds = mock_google_sheet_data_source()

        ret = gsds.get_by_id('object1', [1, 4])
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({'value': 'Value 1', 'optional': 'YES'}, obj1.attributes)
        obj2 = next(ret)
        self.assertEqual(4, obj2.id)
        self.assertEqual({'value': 'Value 4', 'optional': None}, obj2.attributes)
        with self.assertRaises(StopIteration):
            next(ret)
