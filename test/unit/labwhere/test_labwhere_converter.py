# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict
from tol.labwhere.converter import (
    LabwhereApiConverter
)
from tol.labwhere.parser import DefaultParser


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
    to_one: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    data_object._to_one_objects = to_one

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


class TestLabwhereApiConverter:
    """Tests `LabwhereApiConverter().convert()`"""

    def test_no_relationships(self):
        """A resource without relationships"""

        in_ = [
            {
                'location_type_id': 1,
                'barcode': str(i),
                'name': f'name{i}'
            }
            for i in range(4)
        ]

        parser = DefaultParser(_get_mock_ds_dict({'location': {
            'name': 'str'
        }}))
        converter = LabwhereApiConverter(parser)
        (out_, _) = converter.convert_list(in_)

        assert len(out_) == 4
        for i in range(4):
            out_i = out_[i]
            assert out_i.type == 'location'
            assert out_i.id == str(i)
            assert out_i.attributes == {'name': f'name{i}'}

    def test_datetime(self):
        """
        All `datetime` attributes, as defined in
        `LabwhereDataSource().attribute_types`, are parsed.
        """

        now = str(datetime.now())

        in_ = {
            'location_type_id': 2,
            'barcode': 'lol',
            'a': now,
            'b': now,
            'c': now,
            'd': now
        }

        attribute_types = {
            'location': {
                'a': 'datetime',
                'b': 'Date',
                'c': 'tImE',
                # below should not parse as `datetime`
                'd': 'str'
            }
        }

        parser = DefaultParser(
            _get_mock_ds_dict(attribute_types=attribute_types)
        )

        converter = LabwhereApiConverter(parser)

        observed = converter.convert(in_)

        for c in 'abc':
            assert isinstance(
                observed.attributes[c],
                datetime
            )
        assert isinstance(observed.attributes['d'], str)
