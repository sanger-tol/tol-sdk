# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_api_datasource import TestApiDataSource
from ...api_base.test_case import BaseTestCase


class TestListGet(BaseTestCase):
    def test_get_list(self):
        # add two A's
        self.add_a(id=20, string_column='test')
        self.add_a(id=29, string_column='test2')

        # add two B's on the first A
        self.add_b(id=89, a_id=20)
        self.add_b(id=290, a_id=20)

        # add one B on the second A
        self.add_b(id=8080, a_id=29)

        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})
        ret = ads.get_list('b')

        self.assertEqual(3, len(ret))
        b = ret[0]
        self.assertEqual('89', b.id)
        self.assertEqual('b', b.type)
        self.assertEqual('20', b.a.id)
        self.assertEqual('test', b.a.string_column)
        b = ret[1]
        self.assertEqual('290', b.id)
        self.assertEqual('b', b.type)
        self.assertEqual('20', b.a.id)
        self.assertEqual('test', b.a.string_column)
        b = ret[2]
        self.assertEqual('8080', b.id)
        self.assertEqual('b', b.type)
        self.assertEqual('29', b.a.id)
        self.assertEqual('test2', b.a.string_column)
