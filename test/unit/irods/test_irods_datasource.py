# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase, mock)

from tol.irods import IrodsDataSource


class MockIrodsDataSource(IrodsDataSource):
    def _initialise_irods(self):
        self.irods = mock.Mock()

    def _format_results(self, results):
        return results


class TestIrodsDataSource(TestCase):

    def test_get_run_data(self):
        ids = MockIrodsDataSource({
            'host': 'irods.local',
            'port': 1234,
            'user': 'user1',
            'password': 'pass',
            'zone': 'myZone',
            'query_zone': 'anotherZone',
            'extra_config': {'field1': 'value1'}
        })

        mocked_function = ids.irods.query.return_value.add_keyword.return_value \
            .filter.return_value.filter.return_value.get_results
        mocked_function.return_value = [
            {'run_id': '1', 'position': '1', 'tag': '1', 'data_name': 'test.bam'},
            {'run_id': '1', 'position': '2', 'tag': '1', 'data_name': 'test2.bam'},
            {'run_id': '2', 'position': '1', 'tag': '2', 'data_name': 'test3.bam'}
        ]

        results = list(ids.get_run_data(['1234']))
        expected = [{'run_id': '1', 'position': '1', 'tag': '1', 'data_name': 'test.bam'},
                    {'run_id': '1', 'position': '2', 'tag': '1', 'data_name': 'test2.bam'},
                    {'run_id': '2', 'position': '1', 'tag': '2', 'data_name': 'test3.bam'}]
        self.assertEqual(expected, results)

        mocked_function.assert_called_once()
