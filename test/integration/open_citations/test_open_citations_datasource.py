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

    def test_get_list_by_doi_and_pmid(self):
        ods = open_citations()

        objects = list(ods.get_list(
            'meta',
            DataSourceFilter(and_={
                'reference_id': {
                    'in_list': {
                        'value': [
                            '10.1038/nphys1170',
                            'pmid:23287718',
                        ],
                    },
                },
            }),
        ))

        self.assertEqual(
            {obj.id for obj in objects},
            {'10.1038/nphys1170', '10.1126/science.1231143'},
        )
        objects_by_doi = {obj.id: obj for obj in objects}
        pmid_object = objects_by_doi['10.1126/science.1231143']
        self.assertEqual(pmid_object.pmid, '23287718')
        self.assertEqual(
            pmid_object.title,
            'Multiplex Genome Engineering Using CRISPR/Cas Systems',
        )
        self.assertEqual(pmid_object.pub_date, '2013-01-03')
