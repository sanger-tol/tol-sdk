# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import (
    DataSourceFilter
)
from tol.sources.portal import (
    portal
)


class TestPortalDataSource:

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

        ret = pds.get_by_ids('species', ['31033'])
        obj1 = next(ret)
        assert '31033' == obj1.id

        # Just pick out a few attributes here to test
        assert obj1.goat_scientific_name == 'Takifugu rubripes'
        assert obj1.goat_chromosome_number == 44
        assert obj1.goat_assembly_level == 'Chromosome'
        assert obj1.goat_long_list == ['OG', 'VGP']
        assert obj1.goat_phylum_name == 'Chordata'
        assert obj1.tolid_prefix == 'fTakRub'
        with pytest.raises(StopIteration):
            next(ret)

    def test_get_list(self):
        pds = portal(dataspace='tol_production')

        f = DataSourceFilter()
        f.and_ = {
            'goat_long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['254044', '1857951']}}
        }
        ret = list(pds.get_list('species', object_filters=f))
        obj_ids = [obj.id for obj in ret]
        assert '254044' in obj_ids
        assert '1857951' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == '254044':
                assert '254044' == obj.id
                assert obj.goat_scientific_name == 'Oenanthe crocata'
                assert obj.goat_chromosome_number == 22
                assert obj.goat_assembly_level is None
                assert obj.goat_long_list == ['DTOL']
                assert obj.goat_phylum_name == 'Streptophyta'
                assert obj.tolid_prefix == 'drOenCroc'
            elif obj.id == '1857951':
                assert '1857951' == obj.id
                assert obj.goat_scientific_name == 'Acrobasis suavella'
                assert obj.goat_chromosome_number == 60
                assert obj.goat_assembly_level == 'Chromosome'
                assert obj.goat_long_list == ['DTOL', 'PSYCHE']
                assert obj.goat_phylum_name == 'Arthropoda'
                assert obj.goat_sample_collected == ['DTOL']
                assert obj.goat_country_list == [
                    'AT', 'BE', 'BG', 'CA', 'CH', 'DE', 'DK', 'ES', 'FI',
                    'FR', 'GB', 'GR', 'HR', 'IT', 'LU', 'NL', 'PT', 'SE', 'UA', 'US'
                ]
