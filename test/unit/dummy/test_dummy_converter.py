# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict
from tol.dummy.converter import (
    DummyConverter
)
from tol.dummy.parser import DefaultParser


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: Optional[dict[str, Any]] = None,
    to_one: Optional[dict[str, Any]] = None
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes or {}
    data_object.to_one = to_one or {}
    data_object._to_one_objects = to_one or {}

    return data_object


def _get_mock_data_source(
    attribute_types: dict[str, dict[str, Any]] = {}
) -> DataSource:

    mock_ds = create_autospec(DataSource, spec_set=True)

    mock_ds.attribute_types = attribute_types
    mock_ds.supported_types = list(attribute_types.keys())
    mock_ds.data_object_factory = _get_mock_data_object

    return mock_ds


def _get_mock_ds_dict(
    attribute_types: dict[str, dict[str, Any]] = {}
) -> dict[str, DataSource]:

    return DataSourceDict(
        _get_mock_data_source(attribute_types=attribute_types)
    )


class TestDummyConverter:
    """Tests `BoldApiConverter().convert()`"""

    def test_convert_record(self):
        """Test the converter"""

        in_ = [
            {
                'id': 1,
                'big_string': 'a',
                'little_string': 'a',
                'int': 10,
                'date': '2024-05-01',
                'bool': True,
                'type': 'record',
                'category': 'cat1',
                'sub_category': 'cat4',
                'link': 'https://www.google.com/',
                'links': ['https://www.google.com/'],
                'image': {'url': 'https://picsum.photos/200/300', 'caption': 'cap1'},
                'images': [{'url': 'https://picsum.photos/200/300', 'caption': 'cap1'}]
            }
        ]
        parser = DefaultParser(_get_mock_ds_dict({
            'record': {
                'big_string': 'str',
                'little_string': 'str',
                'int': 'int',
                'date': 'datetime',
                'bool': 'bool',
                'list': 'list[str]',
                'link': 'str',
                'links': 'list[str]',
                'image': 'dict[str,str]',
                'images': 'list[dict[str,str]]',
            },
            'category': {
                'name': 'str',
            },
            'sub_category': {
                'name': 'str',
            },
        }))
        converter = DummyConverter(parser)
        (out_, _) = converter.convert_list(in_)
        assert len(out_) == 1
        first = out_[0]
        assert first.type == 'record'
        assert first.id == 1
        print(first.attributes)
        assert first.attributes['big_string'] == 'a'
        assert first.attributes['little_string'] == 'a'
        assert first.attributes['int'] == 10
        assert first.attributes['date'] == datetime.datetime(2024, 5, 1)
        assert first.attributes['bool'] is True
        assert first.attributes['link'] == 'https://www.google.com/'
        assert first.attributes['links'] == ['https://www.google.com/']
        assert first.attributes['image'] == {
            'url': 'https://picsum.photos/200/300',
            'caption': 'cap1',
        }
        assert first.attributes['images'] == [
            {'url': 'https://picsum.photos/200/300', 'caption': 'cap1'}
        ]

        assert first.to_one['category'].type == 'category'
        assert first.to_one['category'].id == 'cat1'

        assert first.to_one['sub_category'].type == 'sub_category'
        assert first.to_one['sub_category'].id == 'cat4'
