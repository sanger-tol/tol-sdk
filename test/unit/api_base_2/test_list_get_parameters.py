# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base2.exception import BadQueryArgError
from tol.api_base2.misc import ListGetParamaters


class TestListGetParameters:
    def test_no_page_size_or_number(self):
        """No page size or page number key specified returns None"""
        parsed = ListGetParamaters({'irrelevent': 'so?'})
        assert parsed.page_size is None
        assert parsed.page_number is None

    def test_good_page_size(self):
        """Just page size, confirm that an integer is returned"""
        parsed = ListGetParamaters({'page_size': '409504'})
        assert parsed.page_size == 409504

    def test_bad_page_size(self):
        """non-positive integer page size raises Exception"""
        for __val in ['0', 'sjdklsjd', '', ' ']:
            with pytest.raises(BadQueryArgError) as e:
                ListGetParamaters({'page_size': __val}).page_size
            assert 'page_size' in str(e.value)
            assert __val in str(e.value)

    def test_good_page_number(self):
        """Just page number, confirm that an integer is returned"""
        parsed = ListGetParamaters({'page_number': '409504'})
        assert parsed.page_number == 409504

    def test_bad_page_number(self):
        """non-positive integer page number raises Exception"""
        for __val in ['0', 'sjdklsjd', '', ' ']:
            with pytest.raises(BadQueryArgError) as e:
                ListGetParamaters({'page_number': __val}).page_number
            assert 'page_number' in str(e.value)
            assert __val in str(e.value)

    def test_page_size_and_number(self):
        """Page size and number specified -> returned correctly"""
        parsed = ListGetParamaters({
            'irrelevent': 'so?',
            'page_number': '2',
            'page_size': '1002'
        })
        assert parsed.page_size == 1002
        assert parsed.page_number == 2
