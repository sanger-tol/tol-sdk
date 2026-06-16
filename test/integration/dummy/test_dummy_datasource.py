# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
from unittest import TestCase

import pytest

from tol.core import DataSourceError
from tol.sources.dummy import dummy


class TestDummyDataSource(TestCase):

    def test_attribute_types(self):
        ds = dummy()

        assert 'record' in ds.attribute_types
        assert 'category' in ds.attribute_types
        assert 'sub_category' in ds.attribute_types

        assert ds.attribute_types['record']['links'] == 'list[str]'
        assert ds.attribute_types['record']['images'] == 'list[dict[str,str]]'
        assert ds.attribute_types['record']['list'] == 'list[str]'
        assert ds.attribute_types['record']['link'] == 'str'
        assert ds.attribute_types['record']['image'] == 'dict[str,str]'

    def test_get_one_record(self):
        ds = dummy()
        obj = ds.get_one('record', '1')

        assert obj is not None
        assert obj.id == '1'
        assert obj.type == 'record'

        # scalar attributes
        assert isinstance(obj.little_string, str)
        assert isinstance(obj.big_string, str)
        assert isinstance(obj.int, int)
        assert isinstance(obj.bool, bool)
        assert isinstance(obj.date, datetime.datetime)
        assert isinstance(obj.link, str)

        # list attributes must be lists
        assert isinstance(obj.links, list)
        assert len(obj.links) == 4
        assert all(isinstance(u, str) for u in obj.links)

        assert isinstance(obj.images, list)
        assert len(obj.images) == 4
        assert all(isinstance(img, dict) for img in obj.images)
        assert all('url' in img and 'caption' in img for img in obj.images)

        assert isinstance(obj.list, list)
        assert len(obj.list) > 0
        assert all(isinstance(w, str) for w in obj.list)

        # image is a single dict
        assert isinstance(obj.image, dict)
        assert 'url' in obj.image and 'caption' in obj.image

        # to-one objects are still set even though this datasource is not Relational
        assert obj._to_one_objects['category'] is not None
        assert obj._to_one_objects['category'].id == 'cat2'  # 1 % 4 == 1 -> index 1
        assert obj._to_one_objects['sub_category'] is not None
        assert obj._to_one_objects['sub_category'].id == 'cat1'  # (1-1) % 4 == 0

    def test_get_one_record_not_found(self):
        ds = dummy()
        obj = ds.get_one('record', '99999')

        assert obj is None

    def test_get_list_record(self):
        ds = dummy()
        records = list(ds.get_list('record'))

        assert len(records) == 20000
        # spot-check first record
        first = records[0]
        assert first.type == 'record'
        assert isinstance(first.links, list)
        assert isinstance(first.images, list)
        assert isinstance(first.list, list)

    def test_get_list_category(self):
        ds = dummy()
        categories = list(ds.get_list('category'))

        assert len(categories) == 4
        assert [c.id for c in categories] == ['cat1', 'cat2', 'cat3', 'cat4']
        assert [c.name for c in categories] == ['CAT1', 'CAT2', 'CAT3', 'CAT4']

    def test_get_list_unsupported_type(self):
        ds = dummy()

        with pytest.raises(DataSourceError):
            list(ds.get_list('nonexistent'))
