# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter
)
from tol.sources.portal import (
    portal
)


class TestPortalDataSource(TestCase):

    def test_supported_types(self):
        pds = portal(dataspace='tol_production')
        assert 'species' in pds.supported_types
        assert 'sample' in pds.supported_types
        assert 'extraction' in pds.supported_types
        assert 'sequencing_request' in pds.supported_types
        assert 'run_data' in pds.supported_types
        assert 'assembly' in pds.supported_types
        assert 'assembly_analysis' in pds.supported_types

        pds = portal(dataspace='test')
        assert 'record' in pds.supported_types

    def test_attribute_types(self):
        pds = portal(dataspace='tol_production')

        assert 'species' in pds.attribute_types
        assert pds.attribute_types['species']['goat_scientific_name'] == 'str'
        assert pds.attribute_types['species']['goat_genome_size'] == 'int'
        assert pds.attribute_types['species']['sts_sample_sts_submit_date_max'] == 'datetime'

    def test_relationship_config(self):
        pds = portal(dataspace='tol_production')

        assert 'sample' in pds.relationship_config
        assert pds.relationship_config['sample'].to_one['sts_species'] == 'species'

    def test_get_by_id(self):
        pds = portal(dataspace='tol_production')

        ret = pds.get_by_ids('species', ['2708'])
        obj1 = next(ret)
        self.assertEqual('2708', obj1.id)

        # Just pick out a few attributes here to test
        self.assertEqual(obj1.goat_scientific_name, 'Citrus x limon')
        self.assertEqual(obj1.goat_chromosome_number, 18)
        self.assertEqual(obj1.goat_assembly_level, 'Chromosome')
        self.assertEqual(obj1.goat_long_list, ['DTOL'])
        self.assertEqual(obj1.goat_phylum_name, 'Streptophyta')
        self.assertEqual(obj1.tolid_prefix, 'drCitLimo')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        pds = portal(dataspace='tol_production')

        f = DataSourceFilter()
        f.and_ = {
            'goat_long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['2708', '1857951']}}
        }
        ret = list(pds.get_list('species', object_filters=f))
        obj_ids = [obj.id for obj in ret]
        assert '2708' in obj_ids
        assert '1857951' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == '2708':
                self.assertEqual('2708', obj.id)
                self.assertEqual(obj.goat_scientific_name, 'Citrus x limon')
                self.assertEqual(obj.goat_chromosome_number, 18)
                self.assertEqual(obj.goat_assembly_level, 'Chromosome')
                self.assertEqual(obj.goat_long_list, ['DTOL'])
                self.assertEqual(obj.goat_phylum_name, 'Streptophyta')
            elif obj.id == '1857951':
                self.assertEqual('1857951', obj.id)
                self.assertEqual(obj.goat_scientific_name, 'Acrobasis suavella')
                self.assertEqual(obj.goat_chromosome_number, 60)
                self.assertEqual(obj.goat_assembly_level, 'Chromosome')
                self.assertEqual(obj.goat_long_list, ['DTOL', 'PSYCHE'])
                self.assertEqual(obj.goat_phylum_name, 'Arthropoda')
                self.assertEqual(obj.goat_sample_collected, ['DTOL'])
                self.assertEqual(
                    obj.goat_country_list,
                    ['AT', 'BE', 'BG', 'CA', 'CH', 'DE', 'DK', 'ES', 'FI', # noqa
                     'FR', 'GB', 'GR', 'HR', 'IT', 'LU', 'NL', 'PT','SE', 'UA', 'US']
                )
