# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter,
    core_data_object
)
from tol.goat import (
    GoatDataSource, create_goat_datasource
)


def goat_data_source() -> GoatDataSource:
    gds = create_goat_datasource(
        goat_url=os.getenv('GOAT_URL') + os.getenv('GOAT_API_PATH')
    )
    cdo = core_data_object(gds)
    return cdo, gds


class TestGoatDataSource(TestCase):

    def test_attribute_types(self):
        _, gds = goat_data_source()

        assert 'taxon' in gds.attribute_types
        assert gds.attribute_types['taxon']['scientific_name'] == 'str'
        assert gds.attribute_types['taxon']['genome_size'] == 'int'
        assert gds.attribute_types['taxon']['family_representative'] == 'List[str]'

    def test_relationship_config(self):
        _, gds = goat_data_source()

        assert 'taxon' in gds.relationship_config
        assert gds.relationship_config['taxon'].to_one['phylum'] == 'taxon'

    def test_get_by_id(self):
        _, gds = goat_data_source()

        ret = gds.get_by_ids('taxon', ['2708'])
        obj1 = next(ret)
        self.assertEqual('2708', obj1.id)
        # Just pick out a few attributes here to test
        self.assertEqual(obj1.scientific_name, 'Citrus x limon')
        self.assertEqual(obj1.chromosome_number, 18)
        self.assertEqual(obj1.long_list, ['DTOL'])
        self.assertEqual(obj1.phylum.scientific_name, 'Streptophyta')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        _, gds = goat_data_source()

        f = DataSourceFilter()
        f.and_ = {
            'long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['2708', '1857951']}}
        }
        ret = gds.get_list('taxon', object_filters=f)
        obj1 = next(ret)
        self.assertEqual('2708', obj1.id)
        self.assertEqual(obj1.scientific_name, 'Citrus x limon')
        self.assertEqual(obj1.chromosome_number, 18)
        self.assertEqual(obj1.long_list, ['DTOL'])
        self.assertEqual(obj1.phylum.scientific_name, 'Streptophyta')

        obj2 = next(ret)
        self.assertEqual('1857951', obj2.id)
        self.assertEqual(obj2.scientific_name, 'Acrobasis suavella')
        self.assertEqual(obj2.chromosome_number, 60)
        self.assertEqual(obj2.long_list, ['DTOL', 'PSYCHE'])
        self.assertEqual(obj2.phylum.scientific_name, 'Arthropoda')

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list_page_sort_custom(self):
        _, gds = goat_data_source()

        f = DataSourceFilter()
        f.and_ = {
            'long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['2708', '62298', '1280447', '1857951']}}
        }
        ret, total = gds.get_list_page(
            'taxon',
            object_filters=f,
            page_number=1,
            page_size=3,
            sort_by='-chromosome_number'
        )
        assert total == 4
        assert len(ret) == 3
        obj2 = ret[0]
        self.assertEqual('1857951', obj2.id)
        self.assertEqual(obj2.scientific_name, 'Acrobasis suavella')
        self.assertEqual(obj2.chromosome_number, 60)
        self.assertEqual(obj2.long_list, ['DTOL', 'PSYCHE'])
        self.assertEqual(obj2.phylum.scientific_name, 'Arthropoda')

        obj3 = ret[1]
        self.assertEqual('1280447', obj3.id)
        self.assertEqual(obj3.scientific_name, 'Acompsia cinerella')
        self.assertEqual(obj3.chromosome_number, 58)
        self.assertEqual(obj3.long_list, ['DTOL', 'PSYCHE'])
        self.assertEqual(obj3.phylum.scientific_name, 'Arthropoda')

        obj1 = ret[2]
        self.assertEqual('2708', obj1.id)
        self.assertEqual(obj1.scientific_name, 'Citrus x limon')
        self.assertEqual(obj1.chromosome_number, 18)
        self.assertEqual(obj1.long_list, ['DTOL'])
        self.assertEqual(obj1.phylum.scientific_name, 'Streptophyta')

    def test_get_list_page_sort_id(self):
        _, gds = goat_data_source()

        f = DataSourceFilter()
        f.and_ = {
            'long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['2708', '62298', '1280447', '1857951']}}
        }
        ret, total = gds.get_list_page(
            'taxon',
            object_filters=f,
            page_number=1,
            page_size=3,
            sort_by='-id'
        )
        assert total == 4
        assert len(ret) == 3
        # It is ordering as strings, not integers
        self.assertEqual('62298', ret[0].id)
        self.assertEqual('2708', ret[1].id)
        self.assertEqual('1857951', ret[2].id)
