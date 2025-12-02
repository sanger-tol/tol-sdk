# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

import pytest

from tol.core import DataObject


@pytest.fixture
def mock_objs() -> Iterable[DataObject]:

    def __mock_obj(c: str) -> DataObject:
        __o: DataObject = create_autospec(
            DataObject,
        )

        __o.id = c
        __o.attributes = {
            'key1': c,
            'key2': c,
            # key 3 is used to test unique_values
            'key3': 'duplicate',
            # key 4 is used to test unique combinations
            'key4': 'other_duplicate'
        }
        __o.key1 = c
        __o.key2 = c

        __o.get_field_by_name.side_effect = lambda field_name: __o.attributes.get(field_name)

        return __o

    return [
        __mock_obj(c) for c in 'abc'
    ]
