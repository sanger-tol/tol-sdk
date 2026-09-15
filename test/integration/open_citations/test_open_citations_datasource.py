# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

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
