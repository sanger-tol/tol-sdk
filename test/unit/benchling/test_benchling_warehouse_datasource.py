# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase, mock)

from tol.benchling import BenchlingWarehouseDataSource
from tol.core import (
    DataSourceError,
    DataSourceFilter,
    core_data_object
)


class MockBenchlingWarehouseDataSource(BenchlingWarehouseDataSource):
    def _get_connection(self):
        return mock.MagicMock()


class TestBenchlingWarehouseDataSource(TestCase):

    def test_get_list(self):
        bds = MockBenchlingWarehouseDataSource(
            {'username': '',
             'password': '',
             'database': '',
             'hostname': '',
             'port': '',
             'schema': ''})
        core_data_object(bds)

        mocked_context_manager = bds.connection.cursor.return_value.__enter__
        mocked_function = mocked_context_manager.return_value.fetchall
        mocked_function.return_value = [
            {'sts_id': '1234', 'priority': '1', 'rack_id': '9876', 'project': 'PROJ1'},
            {'sts_id': '2345', 'position': '2', 'rack_id': '8765', 'project': 'PROJ2'},
            {'sts_id': '3456', 'position': None, 'rack_id': '7654', 'project': 'PROJ3'}
        ]

        # Unsupported object type
        with self.assertRaises(DataSourceError):
            bds.get_list('index')

        # Filtering is unsupported apart from on sequencing_platform and extraction_type
        f = DataSourceFilter()
        with self.assertRaises(DataSourceError):
            bds.get_list('sample', object_filters=f)

        returned = bds.get_list('sample')
        mocked_function.assert_called_once()
        first = next(returned)
        self.assertEqual('1234', first.id)
        self.assertEqual('sample', first.type)
        self.assertEqual({'priority': '1',
                          'rack_id': '9876', 'project': 'PROJ1'},
                         first.attributes)
        second = next(returned)
        self.assertEqual('2345', second.id)
        self.assertEqual('sample', second.type)
        self.assertEqual({'position': '2',
                          'rack_id': '8765', 'project': 'PROJ2'},
                         second.attributes)
        third = next(returned)
        self.assertEqual('3456', third.id)
        self.assertEqual('sample', third.type)
        self.assertEqual({'position': None,
                          'rack_id': '7654', 'project': 'PROJ3'},
                         third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        # Try a sequencing request which has sub-queries
        # No subquery given
        with self.assertRaises(DataSourceError):
            bds.get_list('sequencing_request')
