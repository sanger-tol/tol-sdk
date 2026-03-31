# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib
from datetime import datetime

import pytest

from tol.excel import CsvDataSource


BASE_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture(scope='module')
def object_type() -> str:
    return 'test_indeed'


@pytest.fixture(scope='module')
def type_mapping() -> dict[str, str]:
    return {
        'int_column': 'int',
        'str_column': 'str',
        'bool_column': 'bool',
        'datetime_column': 'datetime',
        # 'float_column': 'float',  # Test default float conversion so don't force type here
    }


class TestTOSEmitter:

    def test_get_list(
        self,
        object_type: str,
        type_mapping: dict[str, str],
    ) -> None:
        """Using a real spreadsheet."""

        sheet_path = BASE_DIR / 'objects.csv'

        emitter = CsvDataSource(
            sheet_path,
            object_type=object_type,
            type_mapping=type_mapping,
        )

        obj1, obj2 = list(
            emitter.get_list(object_type)
        )

        assert obj1.type == object_type
        assert obj1.id == '2'  # Row 2
        dt1 = obj1.attributes.pop('datetime_column')
        assert obj1.attributes == {
            'bool_column': True,
            'float_column': 42.0,
            'int_column': 42,
            'str_column': 'hello',
        }
        assert isinstance(obj1.attributes['float_column'], int)  # test convert to int
        print(dt1)
        assert isinstance(dt1, datetime)
        assert dt1 == datetime(
            year=2000,
            month=2,
            day=18,
        )

        assert obj2.type == object_type
        assert obj2.id == '3'  # Row 3
        dt2 = obj2.attributes.pop('datetime_column')
        assert obj2.attributes == {
            'bool_column': False,
            'float_column': 9032.2,
            'int_column': 9093,
            'str_column': 'world',
        }
        assert isinstance(obj2.attributes['float_column'], float)
        assert isinstance(dt2, datetime)
        assert dt2 == datetime(
            year=2010,
            month=2,
            day=18,
        )
