# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base2.misc import ListGetParamaters
from tol.api_client2.exception import BadQueryArgError


class TestListGetParameters:
    def test_no_parameters(self):
        """No page size or page key specified returns None"""
        parsed = ListGetParamaters({'irrelevent': 'so?'})
        assert parsed.page_size is None
        assert parsed.page is None
        assert parsed.filter is None
        assert parsed.sort_by is None

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
        parsed = ListGetParamaters({'page': '409504'})
        assert parsed.page == 409504

    def test_bad_page_number(self):
        """non-positive integer page number raises Exception"""
        for __val in ['0', 'sjdklsjd', '', ' ']:
            with pytest.raises(BadQueryArgError) as e:
                ListGetParamaters({'page': __val}).page
            assert 'page' in str(e.value)
            assert __val in str(e.value)

    def test_good_filter(self):
        """Just page number, confirm that an integer is returned"""
        filter_string = """
            {"exact": {"column1": "value1"}}
        """
        parsed = ListGetParamaters({'filter': filter_string})
        assert parsed.filter.exact == {'column1': 'value1'}

    def test_bad_filter(self):
        """non-JSON raises Exception"""
        for __val in ['0', 'sjdklsjd', '', ' ']:
            with pytest.raises(BadQueryArgError) as e:
                ListGetParamaters({'filter': __val}).filter
            assert 'filter' in str(e.value)
            assert __val in str(e.value)

    def test_good_sort_by(self):
        """Just page number, confirm that an integer is returned"""
        parsed = ListGetParamaters({'sort_by': '-column1'})
        assert parsed.sort_by == '-column1'

    def test_bad_sort_by(self):
        """non-positive integer page number raises Exception"""
        for __val in ['0', '+sjdklsjd', '', ' ']:
            with pytest.raises(BadQueryArgError) as e:
                ListGetParamaters({'sort_by': __val}).sort_by
            assert 'sort_by' in str(e.value)
            assert __val in str(e.value)

    def test_page_size_and_number(self):
        """Page size and number specified -> returned correctly"""
        parsed = ListGetParamaters({
            'irrelevent': 'so?',
            'page': '2',
            'page_size': '1002'
        })
        assert parsed.page_size == 1002
        assert parsed.page == 2
