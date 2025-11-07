# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (
    TestCase
)

from tol.sources.bold import (
    bold
)


class TestBoldDataSource(TestCase):

    def test_attribute_types(self):
        bds = bold()

        assert 'sample' in bds.attribute_types
        assert bds.attribute_types['sample']['identified_by'] == 'str'
        assert bds.attribute_types['sample']['collection_date_end'] == 'datetime'

    def test_get_by_id_sample(self):
        bds = bold()
        ret = bds.get_by_id('sample', ['CAMP_148_D7', 'Rubbish'])
        obj1 = next(ret)
        assert 'CAMP_148_D7' == obj1.id
        assert obj1.collection_date_start == datetime(2024, 11, 27, 0, 0)
        assert obj1.kingdom == 'Animalia'

        obj2 = next(ret)
        assert obj2 is None

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_by_id_bin(self):
        bds = bold()
        ret = bds.get_by_id('bin', ['BOLD:AAG2462', 'Rubbish'])
        obj1 = next(ret)
        assert 'BOLD:AAG2462' == obj1.id
        assert 'Animalia' in obj1.taxonomy['kingdom']

        obj2 = next(ret)
        assert obj2 is None

        with self.assertRaises(StopIteration):
            next(ret)
