# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase, mock)

from tol.core import (
    DataSourceError,
    DataSourceFilter,
    core_data_object
)
from tol.mlwh import MlwhDataSource


class MockMlwhDataSource(MlwhDataSource):
    def _initialise_mlwh(self):
        self.mlwh = mock.Mock()


class TestMlwhDataSource(TestCase):

    def test_conditions_string(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        in_list = {'study_id': ['one', 'two'],
                   'sample_ref': ['three', 'four']}
        expected = "study.id_study_lims IN ('one','two') AND sample.name IN ('three','four')"
        self.assertEqual(expected, mds._conditions_string('iseq', in_list))

    def test_conditions_string_no_in_list(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        expected = '1=1'
        self.assertEqual(expected, mds._conditions_string('iseq', None))

    def test_get_list_iseq(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        core_data_object(mds)
        in_list = {'study_id': ['one', 'two'],
                   'sample_ref': ['three', 'four']}
        datasource_filter = DataSourceFilter()
        datasource_filter.in_list = in_list
        datasource_filter.exact = {'platform_type': 'iseq'}
        mocked_function = mds.mlwh.cursor.return_value.fetchall
        mocked_function.return_value = [
            {'run_id': '1', 'position': '1', 'tag': '1', 'donor_id': 'Donor 1'},
            {'run_id': '1', 'position': '2', 'tag': '1', 'donor_id': 'Donor 2'},
            {'run_id': '2', 'position': '1', 'tag': '2', 'donor_id': 'Donor 3'}
        ]
        returned = mds.get_list('run_data', datasource_filter)
        first = next(returned)
        self.assertEqual({'run_id': '1', 'position': '1', 'tag': '1',
                          'donor_id': 'Donor 1'}, first.attributes)
        second = next(returned)
        self.assertEqual({'run_id': '1', 'position': '2', 'tag': '1',
                          'donor_id': 'Donor 2'}, second.attributes)
        third = next(returned)
        self.assertEqual({'run_id': '2', 'position': '1', 'tag': '2',
                          'donor_id': 'Donor 3'}, third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        mocked_function.assert_called_once()

    def test_get_list_pacbio_no_in_list_filter(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        core_data_object(mds)
        datasource_filter = DataSourceFilter()
        datasource_filter.exact = {'platform_type': 'pacbio'}
        mocked_function = mds.mlwh.cursor.return_value.fetchall
        mocked_function.return_value = [
            {'run_id': '1', 'position': '1', 'tag': '1', 'donor_id': 'Donor 1'},
            {'run_id': '1', 'position': '2', 'tag': '1', 'donor_id': 'Donor 2'},
            {'run_id': '2', 'position': '1', 'tag': '2', 'donor_id': 'Donor 3'}
        ]
        returned = mds.get_list('run_data', datasource_filter)
        first = next(returned)
        self.assertEqual({'run_id': '1', 'position': '1', 'tag': '1',
                          'donor_id': 'Donor 1'}, first.attributes)
        second = next(returned)
        self.assertEqual({'run_id': '1', 'position': '2', 'tag': '1',
                          'donor_id': 'Donor 2'}, second.attributes)
        third = next(returned)
        self.assertEqual({'run_id': '2', 'position': '1', 'tag': '2',
                          'donor_id': 'Donor 3'}, third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        mocked_function.assert_called_once()

    def test_get_list_no_platform(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        in_list = {'study_id': ['one', 'two'],
                   'sample_ref': ['three', 'four']}
        datasource_filter = DataSourceFilter()
        datasource_filter.in_list = in_list
        # datasource_filter.exact = {'platform_type': 'iseq'}
        with self.assertRaises(DataSourceError):
            mds.get_list('run_data', datasource_filter)

    def test_get_list_not_run_data_or_sequencing_request(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        with self.assertRaises(DataSourceError):
            mds.get_list('something_else')

    def test_get_list_sequencing_request(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        core_data_object(mds)
        in_list = {'study_id': ['one', 'two'],
                   'sample_ref': ['three', 'four']}
        datasource_filter = DataSourceFilter()
        datasource_filter.in_list = in_list
        datasource_filter.exact = {'platform_type': 'iseq'}
        mocked_function = mds.mlwh.cursor.return_value.fetchall
        mocked_function.return_value = [
            {'sample_ref': '1', 'supplier_name': 'Supplier1', 'donor_id': 'Donor 1'},
            {'sample_ref': '2', 'supplier_name': 'Supplier2', 'donor_id': 'Donor 2'},
            {'sample_ref': '3', 'supplier_name': 'Supplier3', 'donor_id': 'Donor 3'}
        ]
        returned = mds.get_list('sequencing_request', datasource_filter)
        first = next(returned)
        self.assertEqual({'sample_ref': '1', 'supplier_name': 'Supplier1',
                          'donor_id': 'Donor 1'}, first.attributes)
        second = next(returned)
        self.assertEqual({'sample_ref': '2', 'supplier_name': 'Supplier2',
                          'donor_id': 'Donor 2'}, second.attributes)
        third = next(returned)
        self.assertEqual({'sample_ref': '3', 'supplier_name': 'Supplier3',
                          'donor_id': 'Donor 3'}, third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        mocked_function.assert_called_once()
