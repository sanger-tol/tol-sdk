# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import math

from ..test_api_datasource import TestApiDataSource
from ...api_base.test_case import BaseTestCase


class TestListGet(BaseTestCase):
    def test_get_list(self):
        c_1 = {
            'id': 9090,
        }
        c_2 = {
            'id': 80808,
            'nullable_column': 'hello, how are you'
        }
        c_3 = {
            'id': 989089,
            'other_column': 'fine, and yourself?'
        }
        self.add_c(**c_1)
        self.add_c(**c_2)
        self.add_c(**c_3)

        ads = TestApiDataSource({'client': self.client,
                                 'key': self.token_1})
        ret = ads.get_list('c')

        self.assertEqual(3, len(ret))
        c = ret[0]
        self.assertEqual('9090', c.id)
        self.assertEqual('c', c.type)
        self.assertIsNone(c.nullable_column)
        self.assertIsNone(c.other_column)
        c = ret[1]
        self.assertEqual('80808', c.id)
        self.assertEqual('c', c.type)
        self.assertEqual('hello, how are you', c.nullable_column)
        self.assertIsNone(c.other_column)
        c = ret[2]
        self.assertEqual('989089', c.id)
        self.assertEqual('c', c.type)
        self.assertIsNone(c.nullable_column)
        self.assertEqual('fine, and yourself?', c.other_column)

    def test_sort(self):
        c_1 = {
            'id': 9090,
        }
        c_2 = {
            'id': 80808,
            'nullable_column': 'hello, how are you'
        }
        c_3 = {
            'id': 989089,
            'nullable_column': 'fine, and yourself?'
        }
        self.add_c(**c_1)
        self.add_c(**c_2)
        self.add_c(**c_3)

        ads = TestApiDataSource({'client': self.client,
                                 'key': self.token_1})
        ret = ads.get_list('c', sort_by='nullable_column')

        self.assertEqual(3, len(ret))
        c = ret[0]
        self.assertEqual('989089', c.id)
        self.assertEqual('c', c.type)
        c = ret[1]
        self.assertEqual('80808', c.id)
        self.assertEqual('c', c.type)
        c = ret[2]
        self.assertEqual('9090', c.id)
        self.assertEqual('c', c.type)

    def test_filter(self):
        c_1 = {
            'id': 9090,
        }
        c_2 = {
            'id': 80808,
            'nullable_column': 'hello, how are you'
        }
        c_3 = {
            'id': 989089,
            'nullable_column': 'fine'
        }
        self.add_c(**c_1)
        self.add_c(**c_2)
        self.add_c(**c_3)

        ads = TestApiDataSource({'client': self.client,
                                 'key': self.token_1})
        ret = ads.get_list('c', filter_='[nullable_column=="fine"]')

        self.assertEqual(1, len(ret))
        c = ret[0]
        self.assertEqual('989089', c.id)
        self.assertEqual('c', c.type)

    def test_paging_one_page(self):
        for i in range(47):
            self.add_c(
                id=i,
                nullable_column='attack of the clones'
            )

        ads = TestApiDataSource({'client': self.client,
                                 'key': self.token_1})
        ret = ads.get_list('c')

        count = 0
        for i in ret:
            self.assertEqual(i.id, str(count))
            count += 1

        self.assertEqual(47, count)

    def test_paging_multiple_pages(self):
        for i in range(472):
            self.add_c(
                id=i,
                nullable_column='attack of the clones'
            )

        ads = TestApiDataSource({'client': self.client,
                                 'key': self.token_1})
        ret = ads.get_list('c')

        count = 0
        for i in ret:
            self.assertEqual(i.id, str(count))
            count += 1
            # Check that we are actually paging
            self.assertEqual(math.ceil(count / 100), ads.get_count)

        self.assertEqual(472, count)

    def test_paging_change_page_size(self):
        for i in range(47):
            self.add_c(
                id=i,
                nullable_column='attack of the clones'
            )

        ads = TestApiDataSource({'client': self.client,
                                 'key': self.token_1})
        ret = ads.get_list('c', page_size=5)

        count = 0
        for i in ret:
            self.assertEqual(i.id, str(count))
            count += 1

        self.assertEqual(47, count)
