# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

from tol.core import (
    DataObject
)
from tol.s3 import S3DataSource


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


class TestS3DataSource:

    def test_supported_types(self):
        expected = ['object']

        ds = S3DataSource(
            None,
            None,
            None,
            None
        )

        observed = ds.supported_types

        assert observed == expected
