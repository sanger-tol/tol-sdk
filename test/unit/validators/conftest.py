# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
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

        def __get_field_by_name(name: str) -> Any:
            match name:
                case 'key1' | 'key2':
                    return c
                case 'key3':
                    return 'duplicate'
                case 'key4':
                    return 'other_duplicate'
        __o.get_field_by_name.side_effect = __get_field_by_name

        return __o

    return [
        __mock_obj(c) for c in 'abc'
    ]
