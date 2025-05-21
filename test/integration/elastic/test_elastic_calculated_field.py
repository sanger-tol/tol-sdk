# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import TestCase

from tol.core import DataSourceFilter
from tol.sources.elastic import elastic


class TestElasticDataSource(TestCase):

    def test_species_calculated_fields(self):
        eds = elastic()

        ret = eds.get_by_ids('species', ['102642'])
        obj = next(ret)
        self.assertEqual('102642', obj.id)

        expected_date = datetime(2024, 6, 29, 1, 0, 25)
        actual_date = datetime.fromtimestamp(obj.calc_done_date / 1000)

        self.assertAlmostEqual(expected_date.timestamp(), actual_date.timestamp(), delta=86400)
        self.assertFalse(obj.calc_is_novel)
        self.assertIn('a. Species on site', obj.calc_pm_status)
        self.assertFalse(obj.calc_specimen_needed_psyche)
        self.assertFalse(obj.calc_recollection_needed)
        self.assertTrue(obj.calc_species_out_for_recollection)

    def test_tolid_calculated_fields(self):
        eds = elastic()

        ret = eds.get_by_ids('tolid', ['icAbaPara2'])
        obj = next(ret)
        self.assertEqual('icAbaPara2', obj.id)

        self.assertAlmostEqual(39.03, obj.calc_coverage, delta=0.1)
        self.assertEqual(0, obj.calc_ongoing_submissions)
        self.assertTrue(obj.calc_coverage_met)
        self.assertFalse(obj.calc_topup_required)
        self.assertTrue(obj.calc_tolid_actionable)
        self.assertFalse(obj.calc_individual_exhausted)
        self.assertFalse(obj.calc_individual_available)

    def test_sample_calculated_fields(self):
        eds = elastic()

        ret = eds.get_by_ids('sample', ['46199'])
        obj = next(ret)
        self.assertEqual('46199', obj.id)

        self.assertEqual('SAMEA112221950', obj.calc_biospecimen_id)
        self.assertTrue(obj.calc_sts_export_eligible)
        self.assertEqual(0, obj.calc_benchling_remaining_weight)

    def test_sequencing_request_calculated_fields(self):
        eds = elastic()

        ret = eds.get_by_ids('sequencing_request', ['DTOL13419005'])
        obj = next(ret)
        self.assertEqual('DTOL13419005', obj.id)

        self.assertAlmostEqual(144.43, obj.calc_existing_library_oplc, delta=0.1)
        self.assertEqual(10, obj.calc_mlwh_volume_remaining)

    def test_extraction_calculated_fields(self):
        eds = elastic()

        ret = eds.get_by_ids('extraction', ['DTOL13419005'])
        obj = next(ret)
        self.assertEqual('DTOL13419005', obj.id)

        self.assertEqual(120, obj.calc_dna_volume_remaining)
        self.assertEqual(0.5, obj.calc_benchling_volume_ul)

    def test_tissue_prep_calculated_fields(self):
        eds = elastic()

        ret = eds.get_by_ids('tissue_prep', ['bfi_U2DTqBw9'])
        obj = next(ret)
        self.assertEqual('bfi_U2DTqBw9', obj.id)

        self.assertEqual(0, obj.calc_benchling_weight_mg)

    def test_get_list_with_calculated_fields(self):
        eds = elastic()

        f = DataSourceFilter()
        f.and_ = {
            'calc_coverage_met': {'eq': {'value': True}},
            'id': {'eq': {'value': 'icAbaPara2'}}
        }
        ret = list(eds.get_list('tolid', object_filters=f))
        self.assertEqual(1, len(ret))
        self.assertEqual('icAbaPara2', ret[0].id)
        self.assertTrue(ret[0].calc_coverage_met)