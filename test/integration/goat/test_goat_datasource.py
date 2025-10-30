# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter
)
from tol.sources.goat import (
    goat
)


class TestGoatDataSource(TestCase):

    def test_attribute_types(self):
        gds = goat()

        assert 'taxon' in gds.attribute_types
        assert gds.attribute_types['taxon']['scientific_name'] == 'str'
        assert gds.attribute_types['taxon']['genome_size'] == 'int'
        assert gds.attribute_types['taxon']['family_representative'] == 'List[str]'
        assert gds.attribute_types['taxon']['synonym'] == 'List[str]'

    def test_relationship_config(self):
        gds = goat()

        assert 'taxon' in gds.relationship_config
        assert gds.relationship_config['taxon'].to_one['phylum'] == 'taxon'

    def test_get_by_id(self):
        gds = goat()

        ret = gds.get_by_ids('taxon', ['4113'])
        obj1 = next(ret)
        self.assertEqual('4113', obj1.id)
        # Just pick out a few attributes here to test
        self.assertEqual(obj1.scientific_name, 'Solanum tuberosum')
        self.assertEqual(obj1.chromosome_number, 48)
        self.assertEqual(obj1.assembly_level, 'Scaffold')
        self.assertEqual(obj1.long_list, ['AFRICABP', 'DTOL'])
        self.assertEqual(obj1.phylum.scientific_name, 'Streptophyta')
        self.assertEqual(obj1.domain.scientific_name, 'Eukaryota')
        self.assertTrue(any('Solanum chocclo' in syn for syn in obj1.synonym))
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        gds = goat()

        f = DataSourceFilter()
        f.and_ = {
            'long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['4113', '1857951']}}
        }
        ret = list(gds.get_list('taxon', object_filters=f))
        obj_ids = [obj.id for obj in ret]
        assert '4113' in obj_ids
        assert '1857951' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == '4113':
                self.assertEqual('4113', obj.id)
                self.assertEqual(obj.scientific_name, 'Solanum tuberosum')
                self.assertEqual(obj.chromosome_number, 48)
                self.assertEqual(obj.assembly_level, 'Scaffold')
                self.assertEqual(obj.long_list, ['AFRICABP', 'DTOL'])
                self.assertEqual(obj.phylum.scientific_name, 'Streptophyta')
                self.assertTrue(any('Solanum chocclo' in syn for syn in obj.synonym))
            elif obj.id == '1857951':
                self.assertEqual('1857951', obj.id)
                self.assertEqual(obj.scientific_name, 'Acrobasis suavella')
                self.assertEqual(obj.chromosome_number, 60)
                self.assertEqual(obj.assembly_level, 'Chromosome')
                self.assertEqual(obj.long_list, ['DTOL', 'PSYCHE'])
                self.assertEqual(obj.phylum.scientific_name, 'Arthropoda')
                self.assertEqual(obj.sample_collected, ['DTOL'])
                self.assertEqual(
                    obj.country_list,
                    ['AT', 'BE', 'BG', 'CA', 'CH', 'DE', 'DK', 'ES', 'FI',
                     'FR', 'GB', 'GR', 'HR', 'IT', 'LU', 'NL', 'PT','SE', 'UA', 'US']
                )
                self.assertTrue(any('Phycis suavella' in syn for syn in obj.synonym))

    def test_get_list_tax_rank(self):
        gds = goat()

        f = DataSourceFilter()
        f.and_ = {
            'taxon_rank': {'eq': {'value': 'species'}},
            'id': {'in_list': {'value': ['9925', '2759']}}
        }
        ret = gds.get_list('taxon', object_filters=f)
        obj1 = next(ret)
        self.assertEqual('9925', obj1.id)
        self.assertEqual(obj1.scientific_name, 'Capra hircus')
        self.assertTrue(any('Capra aegagrus hircus' in syn for syn in obj1.synonym))

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list_scientific_name(self):
        gds = goat()

        f = DataSourceFilter()
        f.and_ = {
            'scientific_name': {'in_list': {'value': ['Capra hircus', 'Mus musculus']}}
        }
        ret = gds.get_list('taxon', object_filters=f)
        # Cannot guarantee order of results
        obj_ids = [obj.id for obj in ret]
        assert '9925' in obj_ids
        assert '10090' in obj_ids
        assert len(obj_ids) == 2

        for obj in ret:
            self.assertIsInstance(obj.synonym, list)
            if len(obj.synonym) > 0:
                self.assertIsInstance(obj.synonym[0], str)

    def test_get_list_page_sort_custom(self):
        gds = goat()

        f = DataSourceFilter()
        f.and_ = {
            'long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['4113', '62298', '687059', '1857951']}}
        }
        ret, total = gds.get_list_page(
            'taxon',
            object_filters=f,
            page_number=1,
            page_size=3,
            sort_by='-scientific_name'
        )
        assert total == 4
        assert len(ret) == 3
        # 687059: Psyche casta
        # 62298: Desmarestia aculeata
        # 2708: Citrus x limon
        # 1857951: Acrobasis suavella
        obj3 = ret[1]
        self.assertEqual('687059', obj3.id)
        self.assertEqual(obj3.scientific_name, 'Psyche casta')
        self.assertEqual(obj3.phylum.scientific_name, 'Arthropoda')
        self.assertTrue(any('Fumaria muscea' in syn for syn in obj3.synonym))

        obj2 = ret[2]
        self.assertEqual('62298', obj2.id)
        self.assertEqual(obj2.scientific_name, 'Desmarestia aculeata')
        self.assertEqual(obj2.family.scientific_name, 'Desmarestiaceae')
        self.assertTrue(any('Fucus virgatus' in syn for syn in obj2.synonym))

        obj1 = ret[0]
        self.assertEqual('4113', obj1.id)
        self.assertEqual(obj1.scientific_name, 'Solanum tuberosum')
        self.assertEqual(obj1.phylum.scientific_name, 'Streptophyta')
        self.assertTrue(any('Solanum chocclo' in syn for syn in obj1.synonym))

    def test_get_list_page_sort_id(self):
        gds = goat()

        f = DataSourceFilter()
        f.and_ = {
            'long_list': {'eq': {'value': 'DTOL'}},
            'id': {'in_list': {'value': ['4113', '62298', '1280447', '1857951']}}
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
        self.assertEqual('4113', ret[1].id)
        self.assertEqual('1857951', ret[2].id)

        for obj in ret:
            self.assertIsInstance(obj.synonym, list)
