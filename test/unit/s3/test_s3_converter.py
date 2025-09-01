# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from minio.datatypes import Object as MinioObject

from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict
from tol.s3.converter import S3Converter
from tol.s3.parser import DefaultParser


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


class TestS3Converter:
    """Tests `S3Converter().convert()`"""

    def test_conversion(self):
        # S3 minio objects we'll try to convert to data sources
        in_ = [
            MinioObject('bucket_one', 'object_one', last_modified=datetime.datetime(2008, 3, 2)),
            MinioObject('bucket_two', 'object_two', last_modified=datetime.datetime(2020, 1, 1))
        ]

        # Perform conversion
        parser = DefaultParser(_get_mock_ds_dict({'object': {
            'bucket_name': 'str',
            'last_modified': 'datetime'
        }}))
        converter = S3Converter(parser)
        out_ = converter.convert_list(in_)

        # Ensure first output data source matches manual conversion
        first = next(out_)
        assert first.type == 'object'
        assert first.id == 'object_one'
        assert first.attributes == {
            'bucket_name': 'bucket_one',
            'last_modified': datetime.datetime(2008, 3, 2)
        }

        # Ensure second output data source matches manual conversion
        second = next(out_)
        assert second.type == 'object'
        assert second.id == 'object_two'
        assert second.attributes == {
            'bucket_name': 'bucket_two',
            'last_modified': datetime.datetime(2020, 1, 1)
        }
