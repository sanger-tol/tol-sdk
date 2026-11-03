# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import (
    DataSourceFilter
)
from tol.sources.api import (
    api
)
from tol.sources.default import (
    default
)

class TestApiDataSource:

    def test_supported_types(self):
        ds = api(
            url='https://quasar.tol.sanger.ac.uk',
            api_path='/api/v1',
            api_data_path='/data',
            dataspace='tol_production'
        )
        assert 'species' in ds.supported_types
        assert 'sample' in ds.supported_types
        assert 'extraction' in ds.supported_types
        assert 'sequencing_request' in ds.supported_types
        assert 'run_data' in ds.supported_types
        assert 'assembly' in ds.supported_types
        assert 'assembly_analysis' in ds.supported_types

        ds = api(
            url='https://quasar.tol.sanger.ac.uk',
            api_path='/api/v1',
            api_data_path='/data',
            dataspace='test'
        )
        assert 'record' in ds.supported_types

    def test_attribute_types(self):
        ds = api(
            url='https://quasar.tol.sanger.ac.uk',
            api_path='/api/v1',
            api_data_path='/data',
            dataspace='tol_production'
        )

        assert 'species' in ds.attribute_types
        assert ds.attribute_types['species']['scientific_name'] == 'str'
        assert ds.attribute_types['species']['genome_size'] == 'int'
        assert ds.attribute_types['species']['sample_submit_date_max'] == 'datetime'

    def test_relationship_config(self):
        ds = api(
            url='https://quasar.tol.sanger.ac.uk',
            api_path='/api/v1',
            api_data_path='/data',
            dataspace='tol_production'
        )

        assert 'sample' in ds.relationship_config
        assert ds.relationship_config['sample'].to_one['species'] == 'species'

    def test_get_by_id(self):
        ds = api(
            url='https://quasar.tol.sanger.ac.uk',
            api_path='/api/v1',
            api_data_path='/data',
            dataspace='tol_production'
        )

        ret = ds.get_by_ids('species', ['31033'])
        obj1 = next(ret)
        assert '31033' == obj1.id

        # Just pick out a few attributes here to test
        assert obj1.scientific_name == 'Takifugu rubripes'
        assert obj1.chromosome_number == 44
        assert obj1.assembly_level == 'Chromosome'
        assert obj1.long_list == ['OG', 'VGP']
        assert obj1.phylum_name == 'Chordata'
        assert obj1.tolid_prefix == 'fTakRub'
        with pytest.raises(StopIteration):
            next(ret)

    def test_get_list(self):
        ds = api(
            url='https://quasar.tol.sanger.ac.uk',
            api_path='/api/v1',
            api_data_path='/data',
            dataspace='tol_production'
        )

        f = DataSourceFilter()
        f.and_ = {
            'long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['254044', '1857951']}}
        }
        ret = list(ds.get_list('species', object_filters=f))
        obj_ids = [obj.id for obj in ret]
        assert '254044' in obj_ids
        assert '1857951' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == '254044':
                assert '254044' == obj.id
                assert obj.scientific_name == 'Oenanthe crocata'
                assert obj.chromosome_number == 22
                assert obj.assembly_level is None
                assert obj.long_list == ['DTOL']
                assert obj.phylum_name == 'Streptophyta'
                assert obj.tolid_prefix == 'drOenCroc'
            elif obj.id == '1857951':
                assert '1857951' == obj.id
                assert obj.scientific_name == 'Acrobasis suavella'
                assert obj.chromosome_number == 60
                assert obj.assembly_level == 'Chromosome'
                assert obj.long_list == ['DTOL', 'PSYCHE']
                assert obj.phylum_name == 'Arthropoda'
                assert obj.sample_collected == ['DTOL']
                assert obj.country_list == [
                    'AT', 'BE', 'BG', 'CA', 'CH', 'DE', 'DK', 'ES', 'FI',
                    'FR', 'GB', 'GR', 'HR', 'IT', 'LU', 'NL', 'PT', 'SE', 'UA', 'US'
                ]
