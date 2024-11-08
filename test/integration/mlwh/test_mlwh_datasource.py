# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter
)
from tol.sources.mlwh import mlwh


class TestMlwhDataSource(TestCase):

    def test_supported_types(self):
        mds = mlwh()

        assert 'run_data' in mds.supported_types
        assert 'sequencing_request' in mds.supported_types
        assert 'long_read_qc_result' in mds.supported_types

    def test_get_list_pacbio(self):
        mds = mlwh()

        f = DataSourceFilter()
        f.and_ = {
            'platform_type': {'eq': {'value': 'pacbio'}},
            'sample_ref': {'in_list': {'value': ['DTOL9502249', 'DTOL9525337']}}
        }
        ret = mds.get_list('run_data', object_filters=f)
        obj1 = next(ret)
        self.assertEqual(obj1.id, 'm64174e_201221_155734#1002')
        self.assertEqual(obj1.sample_ref, 'DTOL9502249')
        self.assertEqual(obj1.scientific_name, 'Euclidia mi')
        self.assertEqual(obj1.run_id, 'm64174e_201221_155734')
        self.assertEqual(obj1.study_id, 5901)
        self.assertEqual(obj1.unique_molecular_bases, 68248375296)

        obj2 = next(ret)
        self.assertEqual(obj2.id, 'm64089_210130_163835#1017')
        self.assertEqual(obj2.sample_ref, 'DTOL9525337')
        self.assertEqual(obj2.scientific_name, 'Ilex aquifolium')
        self.assertEqual(obj2.run_id, 'm64089_210130_163835')
        self.assertEqual(obj2.study_id, 5901)
        self.assertEqual(obj2.unique_molecular_bases, 1482160640)

        obj3 = next(ret)
        self.assertEqual(obj3.id, 'm64125e_210219_152705#1017')
        self.assertEqual(obj3.sample_ref, 'DTOL9525337')
        self.assertEqual(obj3.scientific_name, 'Ilex aquifolium')
        self.assertEqual(obj3.run_id, 'm64125e_210219_152705')
        self.assertEqual(obj3.study_id, 5901)
        self.assertEqual(obj3.unique_molecular_bases, 12384792576)

        obj4 = next(ret)
        self.assertEqual(obj4.id, 'm64016e_210411_202423#1002')
        self.assertEqual(obj4.sample_ref, 'DTOL9502249')
        self.assertEqual(obj4.scientific_name, 'Euclidia mi')
        self.assertEqual(obj4.run_id, 'm64016e_210411_202423')
        self.assertEqual(obj4.study_id, 5901)
        self.assertEqual(obj4.unique_molecular_bases, 52484546560)

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list_illumina(self):
        mds = mlwh()

        f = DataSourceFilter()
        f.and_ = {
            'platform_type': {'eq': {'value': 'Illumina'}},
            'sample_ref': {'in_list': {'value': ['DTOL_RD13133252', 'DTOL13400543']}}
        }
        ret = mds.get_list('run_data', object_filters=f)
        obj1 = next(ret)
        self.assertEqual(obj1.id, '46644_1#83')
        self.assertEqual(obj1.sample_ref, 'DTOL_RD13133252')
        self.assertEqual(obj1.scientific_name, 'Adalia bipunctata')
        self.assertEqual(obj1.run_id, '46644_1')
        self.assertEqual(obj1.study_id, 5822)
        self.assertEqual(obj1.library_id, 'DN881045S:C11')

        obj2 = next(ret)
        self.assertEqual(obj2.id, '47067_4#5')
        self.assertEqual(obj2.sample_ref, 'DTOL13400543')
        self.assertEqual(obj2.scientific_name, 'Glyphipterix thrasonella')
        self.assertEqual(obj2.run_id, '47067_4')
        self.assertEqual(obj2.study_id, 5901)
        self.assertEqual(obj2.library_id, 'SQPP-18544-S:E3')

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_by_id_sequencing_request_volume(self):
        mds = mlwh()
        ret = mds.get_by_id('sequencing_request_volume', ['DTOL14860867', 'DTOL14809561'])
        obj1 = next(ret)
        self.assertEqual(float(obj1.original_volume), 55.4)
        self.assertEqual(obj1.insert_size, 14658)
        self.assertEqual(float(obj1.concentration), 19.06)
        self.assertEqual(float(obj1.volume_remaining), 47.9)
        self.assertEqual(obj1.source_barcode, 'TRAC-2-10395')

        # Has a corrected primary volume (i.e. 2 primary records)
        obj2 = next(ret)
        self.assertEqual(float(obj2.original_volume), 12.9)
        self.assertEqual(obj2.insert_size, 9852)
        self.assertEqual(float(obj2.concentration), 12.8)
        self.assertEqual(float(obj2.volume_remaining), 5.4)
        self.assertEqual(obj2.source_barcode, 'TRAC-2-11696')

        with self.assertRaises(StopIteration):
            next(ret)
