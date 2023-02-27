# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client import ApiObject
from tol.core import DataSourceError

from ..test_api_datasource import TestApiDataSource
from ...api_base.test_case import BaseTestCase


class TestUpdate(BaseTestCase):
    def test_update(self):
        c_1 = {
            'id': 989089,
            'other_column': 'fine'
        }
        self.add_c(**c_1)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})
        cs = list(ads.get_list('c', filter_='{"exact": {"other_column":"fine"}}'))
        self.assertEqual(1, len(cs))
        c = cs[0]
        c.other_column = 'new'
        ads.update(c)
        self.assertEqual(1, ads.patch_count)
        # Check it returns new value
        cs = list(ads.get_list('c', filter_='{"exact": {"other_column":"new"}}'))
        self.assertEqual(1, len(cs))
        c = cs[0]
        self.assertEqual('new', c.other_column)

    def test_update_with_relationship(self):
        self.add_a(id=20, string_column='test')
        self.add_b(id=89, a_id=20)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})

        new_a = ApiObject('a', None,
                          attributes={'string_column': 'abc'})
        ads.create(new_a)

        # Get the b already in the database
        bs = list(ads.get_list('b'))
        self.assertEqual(1, len(bs))
        b = bs[0]
        b.a = new_a
        ads.update(b)

        self.assertEqual(1, ads.patch_count)

        self.assertEqual('abc', b.a.string_column)
        self.assertNotEqual('20', b.a.id)

    def test_update_with_relationship_not_created(self):
        self.add_a(id=20, string_column='test')
        self.add_b(id=89, a_id=20)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})

        new_a = ApiObject('a', None,
                          attributes={'string_column': 'abc'})

        # Get the b already in the database
        bs = list(ads.get_list('b'))
        self.assertEqual(1, len(bs))
        b = bs[0]
        b.a = new_a

        self.assertRaises(DataSourceError, ads.update, b)
        self.assertEqual(1, ads.patch_count)
