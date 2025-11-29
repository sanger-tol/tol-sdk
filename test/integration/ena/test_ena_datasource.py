# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter
)
from tol.sources.ena import (
    ena
)


class TestEnaDataSource(TestCase):

    def test_attribute_types(self):
        eds = ena()

        assert 'taxon' in eds.attribute_types
        assert eds.attribute_types['taxon']['scientific_name'] == 'str'
        assert eds.attribute_types['assembly']['base_count'] == 'float'
        assert eds.attribute_types['sample']['collection_date'] == 'datetime'

    def test_get_by_id(self):
        eds = ena()

        ret = eds.get_by_id('sample', ['SAMEA111431194', 'SAMEA112819851'])
        obj1 = next(ret)
        obj2 = next(ret)

        self.assertEqual(obj1.id, 'SAMEA111431194')
        # Just pick out a few attributes to test
        self.assertEqual(obj1.collection_date, '2022-06-10')
        self.assertEqual(obj1.identified_by, 'MARKUS RUHSAM')
        self.assertEqual(obj2.type, 'sample')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_by_id_checklist(self):
        eds = ena()

        ret = eds.get_by_id('checklist', ['ERC000053', 'ERC000036'])
        obj1 = next(ret)
        obj2 = next(ret)

        self.assertEqual(obj1.id, 'ERC000053')
        # Just pick out a few attributes to test
        self.assertEqual(obj1.checklist.get('specimen_id'), [
            'optional',
            'free text',
            ''
        ])
        self.assertEqual(obj2.type, 'checklist')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        eds = ena()

        f = DataSourceFilter()
        f.and_ = {
            'scientific_name': {'in_list': {'value': ['Capra hircus', 'Mus musculus']}}
        }
        ret = list(eds.get_list('taxon', object_filters=f))
        obj_ids = [obj.id for obj in ret]
        assert '9925' in obj_ids
        assert '10090' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == '9925':
                self.assertEqual(obj.id, '9925')
                # keeps flip-flopping between these two values at ENA
                self.assertIn(obj.common_name, ['domestic goat', 'goats'])
                self.assertEqual(obj.merged_tax_id, '57076')
            elif obj.id == '10090':
                self.assertEqual(obj.id, '10090')
                self.assertEqual(obj.genbank_common_name, 'house mouse')

    def test_get_list_page(self):
        eds = ena()

        f = DataSourceFilter()
        f.and_ = {
            'tax_eq': {'in_list': {'value': ['9662', '74645']}},
            'collection_date': {'lt': {'value': '2024-09-30'}}
        }
        ret, total = eds.get_list_page(
            'assembly',
            object_filters=f,
            page_number=1,
            page_size=4
        )

        assert total == 5
        self.assertEqual(len(ret), 4)
        obj1 = ret[0]
        self.assertEqual(obj1.id, 'GCA_922984935.1')
        self.assertEqual(obj1.collected_by, 'Chris Newman | Ming-shan Tsai | David Macdonald | Christina Buesching | Peter Holland') # noqa
        self.assertEqual(obj1.collection_date, '2019-09-19')

        obj2 = ret[1]
        self.assertEqual(obj2.id, 'GCA_922984935.2')

        obj3 = ret[2]
        self.assertEqual(obj3.id, 'GCA_922990625.1')

        obj4 = ret[3]
        self.assertEqual(obj4.id, 'GCA_958301625.1')
        self.assertEqual(obj4.common_name, 'Japanese rose')
