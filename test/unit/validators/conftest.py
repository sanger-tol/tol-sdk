# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime, time
from typing import Iterable
from unittest.mock import create_autospec

import pytest

from tol.core import DataObject, DataSource, core_data_object


@pytest.fixture
def mock_data_source() -> DataSource:
    class _MockDataSource(DataSource):
        @property
        def supported_types(self):
            return ['upload']

        @property
        def attribute_types(self):
            raise NotImplementedError()

    ds = _MockDataSource(config={})
    core_data_object(ds)
    return ds


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
            'key4': 'other_duplicate',
            'key5': 'x' * 10 if c in 'ac' else 'x' * 20,
            'key6': 'present' if c in 'ab' else None,
            'key7': [c, 'y', 'z'],
            'key8': datetime(2020, 1, 1) if c in 'ab' else datetime(2025, 12, 31),
            'key9': 5.0 if c in 'ab' else 15.0,
            'key10': True if c in 'ab' else False,
            'key11': 10 if c in 'ab' else 20,
            'key12': time(12, 0) if c in 'ab' else time(23, 59),
        }
        __o.key1 = c
        __o.key2 = c

        __o.get_field_by_name.side_effect = lambda field_name: __o.attributes.get(field_name)

        return __o

    return [
        __mock_obj(c) for c in 'abc'
    ]
