# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase, mock)

from tol.core import (
    DataSourceError,
    DataSourceFilter,
    core_data_object
)
from tol.irods import IrodsDataSource


class MockIrodsDataSource(IrodsDataSource):
    def _initialise_irods(self):
        self.irods = mock.Mock()

    def _format_results(self, results):
        return results


class TestIrodsDataSource(TestCase):

    def test_get_list(self):
        ids = MockIrodsDataSource({
            'host': 'irods.local',
            'port': 1234,
            'user': 'user1',
            'password': 'pass',
            'zone': 'myZone',
            'query_zone': 'anotherZone',
            'extra_config': {'field1': 'value1'}
        })
        core_data_object(ids)

        mocked_function = ids.irods.query.return_value.add_keyword.return_value \
            .filter.return_value.filter.return_value.get_results
        mocked_function.return_value = [
            {'run_id': '1234', 'position': '1', 'tag': '1', 'data_name': 'test.bam'},
            {'run_id': '1234', 'position': '2', 'tag': '1', 'data_name': 'test2.bam'},
            {'run_id': '1234', 'position': '2', 'tag': '2', 'data_name': 'test3.bam'}
        ]

        with self.assertRaises(DataSourceError):
            ids.get_list('index')

        f = DataSourceFilter()
        with self.assertRaises(DataSourceError):
            ids.get_list('sequencing_file', object_filters=f)

        f.in_list = {'run_id': ['1234']}
        with self.assertRaises(DataSourceError):
            ids.get_list('sequencing_file', object_filters=f)
        f.exact = {'platform_type': 'iseq'}

        returned = ids.get_list('sequencing_file', object_filters=f)
        first = next(returned)
        self.assertEqual({'run_id': '1234', 'position': '1', 'tag': '1', 'data_name': 'test.bam'},
                         first.attributes)
        second = next(returned)
        self.assertEqual({'run_id': '1234', 'position': '2', 'tag': '1', 'data_name': 'test2.bam'},
                         second.attributes)
        third = next(returned)
        self.assertEqual({'run_id': '1234', 'position': '2', 'tag': '2', 'data_name': 'test3.bam'},
                         third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        f.in_list = {'study_id': ['1234']}
        f.exact = None
        returned = ids.get_list('sequencing_file', object_filters=f)
        first = next(returned)
        self.assertEqual({'run_id': '1234', 'position': '1', 'tag': '1', 'data_name': 'test.bam'},
                         first.attributes)
        second = next(returned)
        self.assertEqual({'run_id': '1234', 'position': '2', 'tag': '1', 'data_name': 'test2.bam'},
                         second.attributes)
        third = next(returned)
        self.assertEqual({'run_id': '1234', 'position': '2', 'tag': '2', 'data_name': 'test3.bam'},
                         third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        self.assertEqual(2, mocked_function.call_count)
