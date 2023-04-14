# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject
from tol.core import DataSourceError

from ..test_api_datasource import TestApiDataSource
from ...api_base.test_case import BaseTestCase


class TestCreate(BaseTestCase):
    def test_create(self):
        c1 = DataObject(
            'c',
            {
                'nullable_column': 'abc',
                'other_column': 'def'
            }
        )
        self.assertIsNone(c1.id)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})
        ads.create(c1)
        self.assertIsNotNone(c1.id)
        self.assertEqual(1, ads.post_count)

    def test_create_with_relationship(self):
        a1 = DataObject('a', None,
                       attributes={'string_column': 'abc'})
        b1 = DataObject('b', None,
                       relationships={'a': a1})
        self.assertIsNone(a1.id)
        self.assertIsNone(b1.id)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})
        ads.create(a1)
        self.assertIsNotNone(a1.id)
        self.assertEqual(1, ads.post_count)
        ads.create(b1)
        self.assertIsNotNone(b1.id)
        self.assertEqual(2, ads.post_count)

    def test_create_with_related_object_not_created(self):
        a1 = DataObject('a', None,
                       attributes={'string_column': 'abc'})
        b1 = DataObject('b', None,
                       relationships={'a': a1})
        self.assertIsNone(a1.id)
        self.assertIsNone(b1.id)
        ads = TestApiDataSource({'client': self.client,
                                 'url': 'none',
                                 'key': self.token_1})
        # a has not been created
        # check that calling ads.create(b1) raises an exception
        self.assertRaises(DataSourceError, ads.create, b1)
        self.assertEqual(1, ads.post_count)
