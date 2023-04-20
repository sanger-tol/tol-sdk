# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client import ApiObject
from tol.core import DataSourceError

from ..test_api_datasource import TestApiDataSource
from ...api_base.test_case import BaseTestCase


class TestDelete(BaseTestCase):
    def test_delete(self):
        g_1 = {
            'id': 989089,
            'string_column': 'fine'
        }
        self.add_g(**g_1)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})
        gs = list(ads.get_list('g', object_filters={'exact': {'string_column': 'fine'}}))
        self.assertEqual(1, len(gs))
        g = gs[0]
        ads.delete(g)
        self.assertEqual(1, ads.delete_count)
        # Check it returns nothing in list_get
        gs = list(ads.get_list('g', object_filters={'exact': {'string_column': 'fine'}}))
        self.assertEqual(0, len(gs))

    def test_delete_with_relationship(self):
        self.add_a(id=20, string_column='test')
        self.add_b(id_string='89', a_id=20)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})

        # Get the b already in the database
        bs = list(ads.get_list('b'))
        self.assertEqual(1, len(bs))
        b = bs[0]
        ads.delete(b)

        self.assertEqual(1, ads.delete_count)

        # Check it returns nothing in list_get
        bs = list(ads.get_list('b'))
        self.assertEqual(0, len(bs))

    def test_delete_no_id(self):
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})

        g1 = ApiObject('g', None,
                       attributes={'string_column': 'test'})

        self.assertRaises(DataSourceError, ads.delete, g1)
        self.assertEqual(0, ads.delete_count)

    def test_delete_non_existing(self):
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})

        g1 = ApiObject('g', 999999,
                       attributes={'string_column': 'test'})

        self.assertRaises(DataSourceError, ads.delete, g1)
        self.assertEqual(1, ads.delete_count)
