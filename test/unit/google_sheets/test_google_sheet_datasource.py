# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (
    TestCase,
    mock
)

from tol.core import (
    DataSourceFilter,
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
                'Optional': 'YES',
                'Boolean': '1',
                'Float': 2.34,
                'Datetime': datetime(2024, 1, 1, 12, 13, 14)
            },
            {
                'Id': 2,
                'Value': 'Value 2',
                'Optional': None,
                'Boolean': '0',
                'Float': None,
                'Datetime': None
            },
            {
                'Id': 3,
                'Value': 'Value 3',
                'Optional': 'NO',
                'Boolean': None,
                'Float': None,
                'Datetime': '14/12/2030'
            },
            {
                'Id': 4,
                'Value': 'Value 4',
                'Optional': None,
                'Boolean': None,
                'Float': None,
                'Datetime': '2024-07-08 13:14:15'
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
    core_data_object_mock = core_data_object(gsds)
    return core_data_object_mock, gsds


class TestGoogleSheetDataSource(TestCase):

    def test_attribute_types(self):
        _, gsds = mock_google_sheet_data_source()
        expected = {
            'object1': {
                'id': 'int',
                'value': 'str',
                'optional': 'str',
                'boolean': 'boolean',
                'float': 'float',
                'datetime': 'datetime'
            }
        }
        self.assertEqual(expected, gsds.attribute_types)
        self.assertEqual(['object1'], gsds.supported_types)

    def test_get_by_id(self):
        _, gsds = mock_google_sheet_data_source()

        ret = gsds.get_by_id('object1', [1, 2, 4])
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 1, 1, 12, 13, 14)}, obj1.attributes)
        obj2 = next(ret)
        self.assertEqual(2, obj2.id)
        self.assertEqual({
            'value': 'Value 2',
            'optional': None,
            'boolean': False,
            'float': None,
            'datetime': None}, obj2.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': None,
            'datetime': datetime(2024, 7, 8, 13, 14, 15)}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        _, gsds = mock_google_sheet_data_source()

        ret = gsds.get_list('object1')
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 1, 1, 12, 13, 14)}, obj1.attributes)
        obj2 = next(ret)
        self.assertEqual(2, obj2.id)
        self.assertEqual({
            'value': 'Value 2',
            'optional': None,
            'boolean': False,
            'float': None,
            'datetime': None}, obj2.attributes)
        obj3 = next(ret)
        self.assertEqual(3, obj3.id)
        self.assertEqual({
            'value': 'Value 3',
            'optional': 'NO',
            'boolean': None,
            'float': None,
            'datetime': datetime(2030, 12, 14)}, obj3.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': None,
            'datetime': datetime(2024, 7, 8, 13, 14, 15)}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_filter_exact(self):
        _, gsds = mock_google_sheet_data_source()

        f = DataSourceFilter()
        f.exact = {'optional': 'YES'}
        ret = gsds.get_list('object1', object_filters=f)
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 1, 1, 12, 13, 14)}, obj1.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_filter_in_list(self):
        _, gsds = mock_google_sheet_data_source()

        f = DataSourceFilter()
        f.in_list = {'optional': ['YES', 'NO']}
        ret = gsds.get_list('object1', object_filters=f)
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 1, 1, 12, 13, 14)}, obj1.attributes)
        obj3 = next(ret)
        self.assertEqual(3, obj3.id)
        self.assertEqual({
            'value': 'Value 3',
            'optional': 'NO',
            'boolean': None,
            'float': None,
            'datetime': datetime(2030, 12, 14)}, obj3.attributes)
        with self.assertRaises(StopIteration):
            next(ret)
