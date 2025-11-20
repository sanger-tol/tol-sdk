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
        self.mlwh = mock.MagicMock()


class TestMlwhDataSource(TestCase):

    def test_conditions_string(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        in_list = {'study_id': ['one', 'two'],
                   'sample_ref': ['three', 'four']}
        expected = "CONVERT(study.id_study_lims, SIGNED) IN ('one','two') " \
            "AND sample.name IN ('three','four')"
        self.assertEqual(expected, mds._conditions_string('illumina', in_list))

    def test_conditions_string_no_in_list(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        expected = '1=1'
        self.assertEqual(expected, mds._conditions_string('illumina', None))

    def test_id_field(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        self.assertEqual('ABC#1001#1002', mds._get_id_from_row({
            'id': 'ABC',
            'platform_type': 'PacBio',
            'tag1_id': '1001',
            'tag2_id': '1002'
        }))
        self.assertEqual('ABC#1008', mds._get_id_from_row({
            'id': 'ABC',
            'platform_type': 'PacBio',
            'tag1_id': 'bc1008_BAK8A_OA',
            'tag2_id': None
        }))
        self.assertEqual('ABC', mds._get_id_from_row({
            'id': 'ABC',
            'platform_type': 'PacBio',
            'tag1_id': None,
            'tag2_id': None
        }))
        self.assertEqual('ABC', mds._get_id_from_row({
            'id': 'ABC',
            'platform_type': 'Illumina',
            'tag1_id': '1001',
            'tag2_id': '1002'
        }))

    def test_get_list_illumina(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        core_data_object(mds)
        f = DataSourceFilter()
        f.and_ = {
            'platform_type': {'eq': {'value': 'Illumina'}},
            'study_id': {'in_list': {'value': ['one', 'two']}},
            'sample_ref': {'in_list': {'value': ['three', 'four']}}
        }
        mocked_function = mds.mlwh.cursor
        mocked_function.return_value.__iter__.return_value = [
            {'id': 'ABC', 'run_id': '1', 'position': '1', 'tag': '1', 'donor_id': 'Donor 1'},
            {'id': 'DEF', 'run_id': '1', 'position': '2', 'tag': '1', 'donor_id': 'Donor 2'},
            {'id': 'GHI', 'run_id': '2', 'position': '1', 'tag': '2', 'donor_id': 'Donor 3'}
        ]
        returned = mds.get_list('run_data', f)
        first = next(returned)
        self.assertEqual('ABC', first.id)
        self.assertEqual({'run_id': '1', 'position': '1', 'tag': '1',
                          'donor_id': 'Donor 1'}, first.attributes)
        second = next(returned)
        self.assertEqual('DEF', second.id)
        self.assertEqual({'run_id': '1', 'position': '2', 'tag': '1',
                          'donor_id': 'Donor 2'}, second.attributes)
        third = next(returned)
        self.assertEqual('GHI', third.id)
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
        f = DataSourceFilter()
        f.and_ = {
            'platform_type': {'eq': {'value': 'PacBio'}}
        }
        mocked_function = mds.mlwh.cursor
        mocked_function.return_value.__iter__.return_value = [
            {'id': 'ABC', 'run_id': '1', 'position': '1', 'tag': '1', 'donor_id': 'Donor 1'},
            {'id': 'DEF', 'run_id': '1', 'position': '2', 'tag': '1', 'donor_id': 'Donor 2'},
            {'id': 'GHI', 'run_id': '2', 'position': '1', 'tag': '2', 'donor_id': 'Donor 3'}
        ]
        returned = mds.get_list('run_data', f)
        first = next(returned)
        self.assertEqual('ABC', first.id)
        self.assertEqual({'run_id': '1', 'position': '1', 'tag': '1',
                          'donor_id': 'Donor 1'}, first.attributes)
        second = next(returned)
        self.assertEqual('DEF', second.id)
        self.assertEqual({'run_id': '1', 'position': '2', 'tag': '1',
                          'donor_id': 'Donor 2'}, second.attributes)
        third = next(returned)
        self.assertEqual('GHI', third.id)
        self.assertEqual({'run_id': '2', 'position': '1', 'tag': '2',
                          'donor_id': 'Donor 3'}, third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        mocked_function.assert_called_once()

    def test_get_list_no_platform(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        f = DataSourceFilter()
        f.and_ = {
            'study_id': {'in_list': {'value': ['one', 'two']}},
            'sample_ref': {'in_list': {'value': ['three', 'four']}}
        }
        with self.assertRaises(DataSourceError):
            mds.get_list('run_data', f)

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
        f = DataSourceFilter()
        f.and_ = {
            'platform_type': {'eq': {'value': 'Illumina'}},
            'study_id': {'in_list': {'value': ['one', 'two']}},
            'sample_ref': {'in_list': {'value': ['three', 'four']}}
        }
        mocked_function = mds.mlwh.cursor
        mocked_function.return_value.__iter__.return_value = [
            {'sample_ref': '1', 'supplier_name': 'Supplier1', 'donor_id': 'Donor 1'},
            {'sample_ref': '2', 'supplier_name': 'Supplier2', 'donor_id': 'Donor 2'},
            {'sample_ref': '3', 'supplier_name': 'Supplier3', 'donor_id': 'Donor 3'}
        ]
        returned = mds.get_list('sequencing_request', f)
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

    def test_get_list_long_read_qc_data(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        core_data_object(mds)
        f = DataSourceFilter()
        mocked_function = mds.mlwh.cursor
        mocked_function.return_value.__iter__.return_value = [
            {'id': 1, 'sample_id': '1', 'assay_type': 'test1', 'value': 'value1'},
            {'id': 2, 'sample_id': '1', 'assay_type': 'test2', 'value': 'value2'},
            {'id': 3, 'sample_id': '2', 'assay_type': 'test1', 'value': 'value3'},
        ]
        returned = mds.get_list('long_read_qc_result', f)
        first = next(returned)
        self.assertEqual({'sample_id': '1', 'assay_type': 'test1',
                          'value': 'value1'}, first.attributes)
        second = next(returned)
        self.assertEqual({'sample_id': '1', 'assay_type': 'test2',
                          'value': 'value2'}, second.attributes)
        third = next(returned)
        self.assertEqual({'sample_id': '2', 'assay_type': 'test1',
                          'value': 'value3'}, third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        mocked_function.assert_called_once()

    def test_get_by_id_sequencing_request_volume(self):
        mds = MockMlwhDataSource({
            'uri': 'mysql://user:pass@host:1234/db'
        })
        core_data_object(mds)
        mocked_function = mds.mlwh.cursor
        mocked_function.return_value.__iter__.return_value = [
            {'id': 1, 'original_volume': 10, 'insert_size': 5, 'concentration': 1,
             'remaining_volume': 5},
            {'id': 2, 'original_volume': 11, 'insert_size': 6, 'concentration': 2,
             'remaining_volume': 6},
            {'id': 3, 'original_volume': 12, 'insert_size': 7, 'concentration': 3,
             'remaining_volume': 7},
        ]
        returned = mds.get_by_id('sequencing_request_volume', ['testId1', 'testId2', 'testId3'])
        first = next(returned)
        self.assertEqual({'original_volume': 10,
                          'insert_size': 5, 'concentration': 1,
                          'remaining_volume': 5}, first.attributes)
        second = next(returned)
        self.assertEqual({'original_volume': 11,
                          'insert_size': 6, 'concentration': 2,
                          'remaining_volume': 6}, second.attributes)
        third = next(returned)
        self.assertEqual({'original_volume': 12,
                          'insert_size': 7, 'concentration': 3,
                          'remaining_volume': 7}, third.attributes)
        with self.assertRaises(StopIteration):
            next(returned)

        mocked_function.assert_called_once()
