# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSourceFilter
from tol.sources.open_citations import open_citations


class TestOpenCitationsDataSource(TestCase):

    def test_get_by_id(self):
        ods = open_citations()

        ret = ods.get_by_id('meta', ['10.1038/nphys1170'])
        obj = next(ret)

        self.assertEqual(obj.id, '10.1038/nphys1170')
        self.assertEqual(obj.type, 'meta')
        self.assertEqual(obj.title, 'Measured Measurement')
        self.assertEqual(obj.pub_date, '2009-01')
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_by_id_not_found(self):
        ods = open_citations()

        ret = ods.get_by_id('meta', ['10.9999/open-citations-missing-record'])

        self.assertIsNone(next(ret))
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_one_by_pmid(self):
        ods = open_citations()

        obj = ods.get_one('meta', 'pmid:23287718')

        self.assertIsNotNone(obj)
        self.assertEqual(obj.id, '10.1126/science.1231143')
        self.assertEqual(obj.type, 'meta')
        self.assertIn('pmid:23287718', obj.attributes['id'])

    def test_get_list_by_doi_and_pmid(self):
        ods = open_citations()

        objects = ods.get_list(
            'meta',
            DataSourceFilter(and_={
                'id': {
                    'in_list': {
                        'value': [
                            '10.1038/nphys1170',
                            'pmid:23287718',
                        ],
                    },
                },
            }),
        )

        self.assertEqual(
            {obj.id for obj in objects},
            {'10.1038/nphys1170', '10.1126/science.1231143'},
        )
